"""
AI Confidence Calibration Layer

Dynamically adjusts acceptance thresholds per field and routes low-confidence
fields to LLM validation or human review.
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FieldThresholds:
    """Confidence thresholds for OCR fields."""
    vendor_min: float = 0.80
    amount_min: float = 0.92
    date_min: float = 0.85
    category_min: float = 0.75
    doc_txn_match_min: float = 0.88


class ConfidenceCalibrator:
    """
    Evaluates OCR field confidence and determines routing.
    
    Routing options:
    - 'accept': Field confidence above threshold
    - 'validate_llm': Field confidence below threshold, route to LLM
    - 'review': Field confidence critically low, route to human
    """
    
    def __init__(self, thresholds: FieldThresholds = None):
        """
        Initialize confidence calibrator.
        
        Args:
            thresholds: Field confidence thresholds
        """
        self.thresholds = thresholds or FieldThresholds()
        logger.info(f"Initialized ConfidenceCalibrator with thresholds: {self.thresholds}")
    
    def evaluate_fields(self, fields: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """
        Evaluate OCR fields and determine routing.
        
        Args:
            fields: Dict of fields with {value, confidence} structure
            
        Returns:
            Dict mapping field names to routing decisions:
            - 'accept': Confidence above threshold
            - 'validate_llm': Confidence below threshold, try LLM
            - 'review': Confidence critically low, needs human review
        """
        decisions = {}
        
        for field_name, field_data in fields.items():
            confidence = field_data.get('confidence', 0.0)
            threshold = self._get_threshold(field_name)
            
            # Determine routing
            if confidence >= threshold:
                decisions[field_name] = 'accept'
            elif confidence >= threshold * 0.7:  # 70% of threshold
                # Low but recoverable - try LLM validation
                decisions[field_name] = 'validate_llm'
            else:
                # Critically low - needs human review
                decisions[field_name] = 'review'
            
            logger.debug(
                f"Field '{field_name}': confidence={confidence:.2f}, "
                f"threshold={threshold:.2f}, decision={decisions[field_name]}"
            )
        
        return decisions
    
    def _get_threshold(self, field_name: str) -> float:
        """Get confidence threshold for field."""
        threshold_map = {
            'vendor': self.thresholds.vendor_min,
            'amount': self.thresholds.amount_min,
            'date': self.thresholds.date_min,
            'category': self.thresholds.category_min,
        }
        return threshold_map.get(field_name, 0.80)
    
    def compute_composite_score(
        self,
        vendor_similarity: float,
        amount_match: float,
        date_match: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Compute composite match score for doc→txn reconciliation.
        
        Args:
            vendor_similarity: Vendor string similarity (0-1)
            amount_match: Amount match score (0-1)
            date_match: Date match score (0-1)
            weights: Optional custom weights
            
        Returns:
            Weighted composite score (0-1)
        """
        if weights is None:
            weights = {
                'vendor': 0.4,
                'amount': 0.4,
                'date': 0.2
            }
        
        composite = (
            vendor_similarity * weights['vendor'] +
            amount_match * weights['amount'] +
            date_match * weights['date']
        )
        
        logger.debug(
            f"Composite score: {composite:.3f} "
            f"(vendor={vendor_similarity:.2f}, amount={amount_match:.2f}, date={date_match:.2f})"
        )
        
        return composite
    
    def should_accept_match(self, composite_score: float) -> bool:
        """Determine if doc→txn match should be accepted."""
        return composite_score >= self.thresholds.doc_txn_match_min
    
    def get_routing_summary(self, decisions: Dict[str, str]) -> Dict[str, int]:
        """Get summary of routing decisions."""
        summary = {
            'accept': 0,
            'validate_llm': 0,
            'review': 0
        }
        
        for decision in decisions.values():
            if decision in summary:
                summary[decision] += 1
        
        return summary
    
    def needs_human_review(self, decisions: Dict[str, str]) -> bool:
        """Check if any field needs human review."""
        return 'review' in decisions.values()
    
    def needs_llm_validation(self, decisions: Dict[str, str]) -> bool:
        """Check if any field needs LLM validation."""
        return 'validate_llm' in decisions.values()


def create_calibrator_from_settings(settings: Any) -> ConfidenceCalibrator:
    """
    Create calibrator from settings object.
    
    Args:
        settings: Settings object with threshold attributes
        
    Returns:
        ConfidenceCalibrator instance
    """
    thresholds = FieldThresholds(
        vendor_min=getattr(settings, 'VENDOR_MIN_CONF', 0.80),
        amount_min=getattr(settings, 'AMOUNT_MIN_CONF', 0.92),
        date_min=getattr(settings, 'DATE_MIN_CONF', 0.85),
        category_min=getattr(settings, 'CATEGORY_MIN_CONF', 0.75),
        doc_txn_match_min=getattr(settings, 'DOC_TXN_MATCH_MIN', 0.88)
    )
    
    return ConfidenceCalibrator(thresholds)

