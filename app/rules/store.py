"""
Rule Store with Versioning and Rollback

Manages immutable rule versions with:
- YAML-based rule storage
- Version history tracking
- Atomic rollback capability
- Dry-run impact analysis
"""
import logging
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.db.models import RuleVersionDB, RuleCandidateDB
from app.rules.schemas import RuleVersion, RuleDefinition

logger = logging.getLogger(__name__)


class RuleStore:
    """
    Manages rule versions with YAML storage and rollback.
    """
    
    def __init__(self, db_session: Any, rules_dir: str = "app/rules/versions"):
        """
        Initialize rule store.
        
        Args:
            db_session: Database session
            rules_dir: Directory for YAML rule files
        """
        self.db = db_session
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"RuleStore initialized: {self.rules_dir}")
    
    def create_version(
        self,
        rules: List[RuleDefinition],
        author: str = "system",
        notes: Optional[str] = None
    ) -> RuleVersion:
        """
        Create a new immutable rule version.
        
        Args:
            rules: List of rule definitions
            author: Version author
            notes: Optional version notes
            
        Returns:
            Created version
        """
        # Generate version ID
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Write YAML file
        yaml_path = self.rules_dir / f"{version_id}.yaml"
        rules_dict = {'rules': [self._rule_to_dict(r) for r in rules]}
        
        with open(yaml_path, 'w') as f:
            yaml.dump(rules_dict, f, sort_keys=False)
        
        # Create DB entry
        version = RuleVersionDB(
            version=version_id,
            author=author,
            path=str(yaml_path),
            rule_count=len(rules),
            notes=notes
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        logger.info(
            f"Created rule version {version_id}: {len(rules)} rules"
        )
        
        return RuleVersion.from_orm(version)
    
    def get_current_version(self) -> Optional[RuleVersion]:
        """Get the most recent rule version."""
        version_db = self.db.query(RuleVersionDB).order_by(
            RuleVersionDB.created_at.desc()
        ).first()
        
        if not version_db:
            return None
        
        return RuleVersion.from_orm(version_db)
    
    def get_version(self, version_id: str) -> Optional[RuleVersion]:
        """Get a specific rule version."""
        version_db = self.db.query(RuleVersionDB).filter_by(
            version=version_id
        ).first()
        
        if not version_db:
            return None
        
        return RuleVersion.from_orm(version_db)
    
    def load_rules(self, version_id: Optional[str] = None) -> List[RuleDefinition]:
        """
        Load rules from a version.
        
        Args:
            version_id: Version to load (current if None)
            
        Returns:
            List of rule definitions
        """
        if version_id:
            version = self.get_version(version_id)
        else:
            version = self.get_current_version()
        
        if not version:
            logger.warning("No rule version found")
            return []
        
        yaml_path = Path(version.path)
        if not yaml_path.exists():
            logger.error(f"Rule file not found: {yaml_path}")
            return []
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        rules = []
        for rule_dict in data.get('rules', []):
            rules.append(RuleDefinition(**rule_dict))
        
        return rules
    
    def rollback(self, version_id: str, author: str = "system") -> RuleVersion:
        """
        Rollback to a previous version by creating a new version.
        
        Args:
            version_id: Version to rollback to
            author: Rollback initiator
            
        Returns:
            New version (copy of specified version)
        """
        # Load rules from target version
        rules = self.load_rules(version_id)
        
        if not rules:
            raise ValueError(f"Version {version_id} has no rules or not found")
        
        # Create new version with same rules
        new_version = self.create_version(
            rules,
            author=author,
            notes=f"Rollback to {version_id}"
        )
        
        logger.info(f"Rolled back to {version_id}, created {new_version.version}")
        
        return new_version
    
    def promote_accepted_candidates(self, author: str = "system") -> RuleVersion:
        """
        Promote all accepted candidates to a new rule version.
        
        Args:
            author: Version author
            
        Returns:
            New version with promoted rules
        """
        # Load current rules
        current_rules = self.load_rules()
        
        # Get accepted candidates
        candidates = self.db.query(RuleCandidateDB).filter_by(
            status='accepted'
        ).all()
        
        if not candidates:
            logger.info("No accepted candidates to promote")
            return self.get_current_version()
        
        # Convert candidates to rules
        new_rules = []
        for candidate in candidates:
            rule = RuleDefinition(
                id=f"promoted_{candidate.id}",
                type="exact_vendor",
                pattern=candidate.vendor_normalized,
                account=candidate.suggested_account,
                confidence=candidate.avg_confidence,
                priority=50,  # Lower priority than exact matches
                enabled=True,
                created_at=datetime.now(),
                metadata={
                    'promoted_from_candidate': candidate.id,
                    'obs_count': candidate.obs_count,
                    'avg_confidence': candidate.avg_confidence
                }
            )
            new_rules.append(rule)
        
        # Combine with existing rules
        all_rules = current_rules + new_rules
        
        # Create new version
        version = self.create_version(
            all_rules,
            author=author,
            notes=f"Promoted {len(new_rules)} candidates"
        )
        
        logger.info(f"Promoted {len(new_rules)} candidates to {version.version}")
        
        return version
    
    def dry_run_impact(
        self,
        new_rules: List[RuleDefinition],
        test_transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate impact of new rules without applying them.
        
        Args:
            new_rules: Proposed rules
            test_transactions: Transactions to test against
            
        Returns:
            Impact analysis
        """
        current_rules = self.load_rules()
        
        # Evaluate current automation
        current_matches = self._evaluate_rules(current_rules, test_transactions)
        current_auto = sum(1 for m in current_matches if m['matched'])
        
        # Evaluate with new rules
        combined_rules = current_rules + new_rules
        new_matches = self._evaluate_rules(combined_rules, test_transactions)
        new_auto = sum(1 for m in new_matches if m['matched'])
        
        # Detect conflicts
        conflicts = []
        for i, (curr, new) in enumerate(zip(current_matches, new_matches)):
            if curr['matched'] and new['matched']:
                if curr['account'] != new['account']:
                    conflicts.append({
                        'txn_index': i,
                        'old_account': curr['account'],
                        'new_account': new['account']
                    })
        
        total = len(test_transactions)
        current_pct = (current_auto / total * 100) if total > 0 else 0.0
        new_pct = (new_auto / total * 100) if total > 0 else 0.0
        
        return {
            'automation_pct_before': current_pct,
            'automation_pct_after': new_pct,
            'automation_pct_delta': new_pct - current_pct,
            'conflicts': len(conflicts),
            'affected_transactions': new_auto - current_auto,
            'safety_flags': self._check_safety(conflicts),
            'sample_changes': conflicts[:10]  # First 10 conflicts
        }
    
    @staticmethod
    def _rule_to_dict(rule: RuleDefinition) -> Dict[str, Any]:
        """Convert rule to dict for YAML."""
        return {
            'id': rule.id,
            'type': rule.type,
            'pattern': rule.pattern,
            'account': rule.account,
            'confidence': rule.confidence,
            'priority': rule.priority,
            'enabled': rule.enabled,
            'metadata': rule.metadata
        }
    
    @staticmethod
    def _evaluate_rules(
        rules: List[RuleDefinition],
        transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate rules against transactions (simplified).
        
        Returns list of matches per transaction.
        """
        matches = []
        for txn in transactions:
            vendor = txn.get('vendor', '').lower()
            matched = False
            account = None
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                if rule.type == "exact_vendor":
                    if rule.pattern.lower() == vendor:
                        matched = True
                        account = rule.account
                        break
            
            matches.append({
                'matched': matched,
                'account': account
            })
        
        return matches
    
    @staticmethod
    def _check_safety(conflicts: List[Dict[str, Any]]) -> List[str]:
        """Check for safety concerns in conflicts."""
        flags = []
        
        if len(conflicts) > 10:
            flags.append("HIGH_CONFLICT_COUNT")
        
        # Check for systematic reclassification
        reclassifications = defaultdict(set)
        for conflict in conflicts:
            reclassifications[conflict['old_account']].add(conflict['new_account'])
        
        for old, news in reclassifications.items():
            if len(news) > 3:
                flags.append(f"SYSTEMATIC_RECLASSIFICATION: {old}")
        
        return flags


def create_rule_store(db_session: Any, rules_dir: str = "app/rules/versions") -> RuleStore:
    """Factory to create rule store."""
    return RuleStore(db_session, rules_dir)


# For collections.defaultdict
from collections import defaultdict

