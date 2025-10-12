"""
Hybrid Decision Engine.

Routing logic:
1. Rules Engine (regex/exact match)
2. ML Classifier (if confidence >= threshold)
3. LLM (fallback)
4. Human Review (if all fail or low confidence)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Hybrid decision engine for transaction categorization."""
    
    def __init__(
        self,
        use_rules: bool = True,
        use_ml: bool = True,
        use_llm: bool = False,  # Disabled by default (mock mode)
        ml_threshold: float = 0.85,
        llm_threshold: float = 0.85
    ):
        """
        Initialize decision engine.
        
        Args:
            use_rules: Enable rules engine
            use_ml: Enable ML classifier
            use_llm: Enable LLM (requires API key)
            ml_threshold: Confidence threshold for ML auto-approval
            llm_threshold: Confidence threshold for LLM auto-approval
        """
        self.use_rules = use_rules
        self.use_ml = use_ml
        self.use_llm = use_llm
        self.ml_threshold = ml_threshold
        self.llm_threshold = llm_threshold
        
        # Lazy-load components
        self.rules_engine = None
        self.ml_classifier = None
        self.llm_categorizer = None
        
        # Stats
        self.stats = {
            'rules_matches': 0,
            'ml_matches': 0,
            'llm_matches': 0,
            'manual_review': 0
        }
    
    def _get_rules_engine(self):
        """Lazy-load rules engine."""
        if self.rules_engine is None and self.use_rules:
            from app.rules.engine import RulesEngine
            self.rules_engine = RulesEngine()
        return self.rules_engine
    
    def _get_ml_classifier(self):
        """Lazy-load ML classifier."""
        if self.ml_classifier is None and self.use_ml:
            from app.ml.classifier import get_classifier
            self.ml_classifier = get_classifier()
        return self.ml_classifier
    
    def _get_llm_categorizer(self):
        """Lazy-load LLM categorizer."""
        if self.llm_categorizer is None and self.use_llm:
            try:
                from app.llm.categorize_post import llm_categorizer
                self.llm_categorizer = llm_categorizer
            except Exception as e:
                logger.warning(f"LLM not available: {e}")
                self.use_llm = False
        return self.llm_categorizer
    
    def categorize(
        self,
        amount: float,
        description: str,
        counterparty: str,
        date: date,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Categorize a transaction using hybrid approach.
        
        Args:
            amount: Transaction amount
            description: Transaction description
            counterparty: Counterparty/vendor name
            date: Transaction date
            company_id: Company identifier (optional)
            
        Returns:
            Dict with:
                - account: Predicted account
                - confidence: Confidence score (0-1)
                - method: Which method was used (rules/ml/llm/manual)
                - needs_review: Whether human review is required
                - rationale: Explanation of decision
        """
        # Prepare transaction object for rules engine (expects object with attributes)
        from app.db.models import Transaction
        transaction_obj = Transaction(
            txn_id="temp",
            date=date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date),
            amount=amount,
            description=description,
            counterparty=counterparty,
            currency="USD",
            raw={}
        )
        
        # ====================================================================
        # STEP 1: Try Rules Engine
        # ====================================================================
        if self.use_rules:
            rules_engine = self._get_rules_engine()
            if rules_engine:
                try:
                    match = rules_engine.match_transaction(transaction_obj)
                    if match and match.get('account'):
                        self.stats['rules_matches'] += 1
                        return {
                            'account': match['account'],
                            'confidence': match.get('confidence', 1.0),
                            'method': 'rules',
                            'needs_review': False,
                            'rationale': match.get('rationale', f"Matched rule: {match.get('rule_name', 'unknown')}")
                        }
                except Exception as e:
                    logger.error(f"Rules engine error: {e}")
        
        # ====================================================================
        # STEP 2: Try ML Classifier
        # ====================================================================
        if self.use_ml:
            ml_classifier = self._get_ml_classifier()
            if ml_classifier and ml_classifier.is_loaded:
                try:
                    account, probability = ml_classifier.predict(
                        description=description,
                        counterparty=counterparty or "",
                        amount=amount,
                        date=datetime.strptime(str(date), '%Y-%m-%d') if isinstance(date, str) else date
                    )
                    
                    if probability >= self.ml_threshold:
                        self.stats['ml_matches'] += 1
                        return {
                            'account': account,
                            'confidence': probability,
                            'method': 'ml',
                            'needs_review': False,
                            'rationale': f"ML classifier (probability: {probability:.2%})"
                        }
                    elif probability >= 0.70:
                        # Medium confidence - suggest but require review
                        return {
                            'account': account,
                            'confidence': probability,
                            'method': 'ml_review',
                            'needs_review': True,
                            'rationale': f"ML classifier (probability: {probability:.2%}, below threshold)"
                        }
                except Exception as e:
                    logger.error(f"ML classifier error: {e}")
        
        # ====================================================================
        # STEP 3: Try LLM
        # ====================================================================
        if self.use_llm:
            llm = self._get_llm_categorizer()
            if llm:
                try:
                    # Mock LLM response for now
                    result = self._mock_llm_categorize(transaction)
                    
                    if result['confidence'] >= self.llm_threshold:
                        self.stats['llm_matches'] += 1
                        return {
                            'account': result['account'],
                            'confidence': result['confidence'],
                            'method': 'llm',
                            'needs_review': result.get('needs_review', False),
                            'rationale': result.get('rationale', 'LLM categorization')
                        }
                except Exception as e:
                    logger.error(f"LLM error: {e}")
        
        # ====================================================================
        # STEP 4: Manual Review
        # ====================================================================
        self.stats['manual_review'] += 1
        
        # Return a default guess based on amount
        default_account = "8000 Sales Revenue" if amount > 0 else "6100 Office Supplies"
        
        return {
            'account': default_account,
            'confidence': 0.50,
            'method': 'fallback',
            'needs_review': True,
            'rationale': 'No high-confidence match found, manual review required'
        }
    
    def _mock_llm_categorize(self, transaction) -> Dict[str, Any]:
        """Mock LLM categorization (same as Sprint 3 heuristics)."""
        desc = transaction.description.lower() if hasattr(transaction, 'description') else str(transaction.get('description', '')).lower()
        amount = transaction.amount if hasattr(transaction, 'amount') else transaction.get('amount', 0)
        
        if amount > 0:
            if any(word in desc for word in ["square", "stripe", "paypal", "payment"]):
                return {
                    "account": "8000 Sales Revenue",
                    "confidence": 0.88,
                    "needs_review": False,
                    "rationale": "Heuristic: Payment processor revenue"
                }
            else:
                return {
                    "account": "8000 Sales Revenue",
                    "confidence": 0.75,
                    "needs_review": False,
                    "rationale": "Heuristic: Positive amount (revenue)"
                }
        
        if "aws" in desc or "cloud" in desc or "digital ocean" in desc:
            return {
                "account": "6300 Software Subscriptions",
                "confidence": 0.92,
                "needs_review": False,
                "rationale": "Heuristic: Cloud/SaaS expense"
            }
        elif "ads" in desc or "google" in desc or "facebook" in desc or "marketing" in desc:
            return {
                "account": "7000 Marketing & Advertising",
                "confidence": 0.90,
                "needs_review": False,
                "rationale": "Heuristic: Advertising expense"
            }
        elif "payroll" in desc or "adp" in desc or "paychex" in desc:
            return {
                "account": "6400 Payroll Expenses",
                "confidence": 0.95,
                "needs_review": False,
                "rationale": "Heuristic: Payroll expense"
            }
        elif "utility" in desc or "electric" in desc or "gas" in desc or "water" in desc:
            return {
                "account": "6200 Utilities",
                "confidence": 0.93,
                "needs_review": False,
                "rationale": "Heuristic: Utilities expense"
            }
        elif "amazon" in desc or "office" in desc or "supplies" in desc:
            return {
                "account": "6100 Office Supplies",
                "confidence": 0.85,
                "needs_review": False,
                "rationale": "Heuristic: Office supplies"
            }
        else:
            return {
                "account": "6100 Office Supplies",
                "confidence": 0.70,
                "needs_review": True,
                "rationale": "Heuristic: General expense (low confidence)"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        total = sum(self.stats.values())
        
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'total': total,
            'rules_pct': self.stats['rules_matches'] / total * 100,
            'ml_pct': self.stats['ml_matches'] / total * 100,
            'llm_pct': self.stats['llm_matches'] / total * 100,
            'manual_pct': self.stats['manual_review'] / total * 100
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            'rules_matches': 0,
            'ml_matches': 0,
            'llm_matches': 0,
            'manual_review': 0
        }

