"""
Adaptive Rule Promoter

Automatically learns and proposes new rules from:
- User overrides
- ML/LLM disagreements
- Recurring patterns

Evidence-based promotion with configurable thresholds.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import numpy as np

from app.db.models import RuleCandidateDB
from app.rules.schemas import (
    RuleEvidence, RuleCandidate, PromotionPolicy
)

logger = logging.getLogger(__name__)


class RulePromoter:
    """
    Manages candidate rule detection and promotion.
    """
    
    def __init__(self, db_session: Any, policy: Optional[PromotionPolicy] = None):
        """
        Initialize rule promoter.
        
        Args:
            db_session: Database session
            policy: Promotion policy (uses defaults if None)
        """
        self.db = db_session
        self.policy = policy or PromotionPolicy()
        
        logger.info(
            f"RulePromoter initialized: "
            f"min_obs={self.policy.min_observations}, "
            f"min_conf={self.policy.min_confidence}"
        )
    
    def add_evidence(self, evidence: RuleEvidence) -> Dict[str, Any]:
        """
        Add evidence for a potential rule.
        
        Args:
            evidence: Evidence from user override or model disagreement
            
        Returns:
            Dict with candidate status
        """
        # Normalize vendor name
        vendor_norm = self._normalize_vendor(evidence.vendor_normalized)
        
        # Find or create candidate
        candidate = self.db.query(RuleCandidateDB).filter_by(
            vendor_normalized=vendor_norm,
            suggested_account=evidence.suggested_account,
            status='pending'
        ).first()
        
        if not candidate:
            candidate = RuleCandidateDB(
                vendor_normalized=vendor_norm,
                suggested_account=evidence.suggested_account,
                obs_count=0,
                avg_confidence=0.0,
                variance=0.0,
                reasons_json={'evidence': []}
            )
            self.db.add(candidate)
        
        # Update statistics
        n = candidate.obs_count
        old_mean = candidate.avg_confidence
        new_value = evidence.confidence
        
        # Incremental mean
        new_mean = (n * old_mean + new_value) / (n + 1)
        
        # Incremental variance (Welford's algorithm)
        if n == 0:
            new_var = 0.0
        else:
            old_var = candidate.variance
            new_var = ((n - 1) * old_var + (new_value - old_mean) * (new_value - new_mean)) / n
        
        candidate.obs_count = n + 1
        candidate.avg_confidence = new_mean
        candidate.variance = new_var
        candidate.last_seen_at = evidence.timestamp
        
        # Append evidence
        if not candidate.reasons_json:
            candidate.reasons_json = {'evidence': []}
        candidate.reasons_json['evidence'].append({
            'source': evidence.source,
            'txn_id': evidence.transaction_id,
            'confidence': evidence.confidence,
            'timestamp': evidence.timestamp.isoformat()
        })
        
        self.db.commit()
        
        # Check if ready for promotion
        ready = self._check_promotion_criteria(candidate)
        
        return {
            'candidate_id': candidate.id,
            'vendor': vendor_norm,
            'account': candidate.suggested_account,
            'obs_count': candidate.obs_count,
            'avg_confidence': candidate.avg_confidence,
            'variance': candidate.variance,
            'ready_for_promotion': ready
        }
    
    def _check_promotion_criteria(self, candidate: RuleCandidateDB) -> bool:
        """
        Check if candidate meets promotion criteria.
        
        Args:
            candidate: Candidate rule
            
        Returns:
            True if ready for promotion
        """
        if candidate.obs_count < self.policy.min_observations:
            return False
        
        if candidate.avg_confidence < self.policy.min_confidence:
            return False
        
        if candidate.variance > self.policy.max_variance:
            return False
        
        return True
    
    def get_candidates(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[RuleCandidate]:
        """
        Get candidate rules.
        
        Args:
            status: Filter by status ('pending', 'accepted', 'rejected')
            limit: Max results
            offset: Skip offset results
            
        Returns:
            List of candidates
        """
        query = self.db.query(RuleCandidateDB)
        
        if status:
            query = query.filter_by(status=status)
        
        candidates = query.order_by(
            RuleCandidateDB.obs_count.desc()
        ).limit(limit).offset(offset).all()
        
        return [RuleCandidate.from_orm(c) for c in candidates]
    
    def accept_candidate(
        self,
        candidate_id: int,
        decided_by: str = "system",
        edited_account: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Accept a candidate rule.
        
        Args:
            candidate_id: Candidate ID
            decided_by: User or system identifier
            edited_account: Optional edited account (overrides suggested)
            
        Returns:
            Accepted rule details
        """
        candidate = self.db.query(RuleCandidateDB).filter_by(
            id=candidate_id
        ).first()
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        if candidate.status != 'pending':
            raise ValueError(f"Candidate {candidate_id} already decided: {candidate.status}")
        
        # Apply edit if provided
        final_account = edited_account or candidate.suggested_account
        
        candidate.status = 'accepted'
        candidate.decided_by = decided_by
        candidate.decided_at = datetime.now()
        
        if edited_account:
            candidate.suggested_account = edited_account
        
        self.db.commit()
        
        logger.info(
            f"Accepted rule candidate {candidate_id}: "
            f"{candidate.vendor_normalized} → {final_account}"
        )
        
        return {
            'candidate_id': candidate_id,
            'vendor': candidate.vendor_normalized,
            'account': final_account,
            'obs_count': candidate.obs_count,
            'decided_by': decided_by
        }
    
    def reject_candidate(
        self,
        candidate_id: int,
        reason: str,
        decided_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Reject a candidate rule.
        
        Args:
            candidate_id: Candidate ID
            reason: Rejection reason
            decided_by: User or system identifier
            
        Returns:
            Rejection details
        """
        candidate = self.db.query(RuleCandidateDB).filter_by(
            id=candidate_id
        ).first()
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        if candidate.status != 'pending':
            raise ValueError(f"Candidate {candidate_id} already decided: {candidate.status}")
        
        candidate.status = 'rejected'
        candidate.decided_by = decided_by
        candidate.decided_at = datetime.now()
        
        if not candidate.reasons_json:
            candidate.reasons_json = {}
        candidate.reasons_json['rejection_reason'] = reason
        
        self.db.commit()
        
        logger.info(
            f"Rejected rule candidate {candidate_id}: "
            f"{candidate.vendor_normalized}, reason: {reason}"
        )
        
        return {
            'candidate_id': candidate_id,
            'vendor': candidate.vendor_normalized,
            'reason': reason,
            'decided_by': decided_by
        }
    
    def auto_promote_ready_candidates(self) -> List[Dict[str, Any]]:
        """
        Automatically promote candidates that meet criteria.
        
        Returns:
            List of promoted candidates
        """
        candidates = self.db.query(RuleCandidateDB).filter_by(
            status='pending'
        ).all()
        
        promoted = []
        for candidate in candidates:
            if self._check_promotion_criteria(candidate):
                try:
                    result = self.accept_candidate(
                        candidate.id,
                        decided_by="auto_promoter"
                    )
                    promoted.append(result)
                except Exception as e:
                    logger.error(f"Auto-promotion failed for {candidate.id}: {e}")
        
        logger.info(f"Auto-promoted {len(promoted)} candidates")
        
        return promoted
    
    @staticmethod
    def _normalize_vendor(vendor: str) -> str:
        """Normalize vendor name for consistent matching."""
        return vendor.lower().strip().replace('  ', ' ')


def create_rule_promoter(db_session: Any, policy: Optional[PromotionPolicy] = None) -> RulePromoter:
    """
    Factory function to create rule promoter.
    
    Args:
        db_session: Database session
        policy: Optional promotion policy
        
    Returns:
        RulePromoter instance
    """
    return RulePromoter(db_session, policy)

