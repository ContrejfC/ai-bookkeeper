"""
Confidence Scoring
==================

Calculate confidence scores for extracted transactions with review flagging.
"""

import logging
from typing import List, Dict, Any, Tuple
from decimal import Decimal

from app.ingestion.config import config
from app.ingestion.schemas import CanonicalTransaction, ConfidenceScore

logger = logging.getLogger(__name__)


# Extraction method base confidence weights
EXTRACTION_WEIGHTS = {
    'pdf_template': 0.95,  # Bank-specific template match
    'pdf_text': 0.90,      # Clean text extraction
    'pdf_layout': 0.85,    # Layout-based grid extraction
    'csv': 0.88,           # CSV with good headers
    'ofx': 0.92,           # Structured OFX format
    'ocr_grid': 0.75,      # OCR with grid detection
    'ocr_line': 0.60,      # Line-by-line OCR (last resort)
    'image': 0.70,         # Image OCR
    'unknown': 0.50,       # Unknown extraction method
}


def calculate_confidence(
    transaction: CanonicalTransaction,
    extraction_method: str,
    metadata: Dict[str, Any] = None
) -> ConfidenceScore:
    """
    Calculate confidence score for a transaction.
    
    Args:
        transaction: Canonical transaction
        extraction_method: Extraction method used
        metadata: Additional metadata from extraction
    
    Returns:
        ConfidenceScore with breakdown
    """
    metadata = metadata or {}
    
    # Start with base extraction method weight
    extraction_score = EXTRACTION_WEIGHTS.get(extraction_method, 0.5)
    
    # Calculate normalization score
    normalization_score = _calculate_normalization_score(transaction)
    
    # Calculate reconciliation score (from metadata)
    reconciliation_score = 1.0 if metadata.get('reconciliation_passed', True) else 0.0
    
    # Calculate component scores
    factors = {
        'extraction_method': extraction_score,
        'normalization': normalization_score,
        'reconciliation': reconciliation_score,
    }
    
    # Add metadata-based factors
    if 'header_match_score' in metadata:
        factors['header_match'] = metadata['header_match_score']
    
    if 'table_confidence' in metadata:
        factors['table_detection'] = metadata['table_confidence']
    
    if 'ocr_char_confidence' in metadata:
        factors['ocr_quality'] = metadata['ocr_char_confidence']
    
    # Weighted average of all factors
    weights = {
        'extraction_method': 0.40,
        'normalization': 0.30,
        'reconciliation': 0.20,
        'header_match': 0.05,
        'table_detection': 0.03,
        'ocr_quality': 0.02,
    }
    
    overall = 0.0
    total_weight = 0.0
    
    for factor, score in factors.items():
        weight = weights.get(factor, 0.01)
        overall += score * weight
        total_weight += weight
    
    # Normalize
    if total_weight > 0:
        overall = overall / total_weight
    
    # Apply penalties
    penalties = _calculate_penalties(transaction, metadata)
    for penalty in penalties:
        overall *= (1.0 - penalty['amount'])
    
    # Clamp to [0, 1]
    overall = max(0.0, min(1.0, overall))
    
    # Determine if needs review
    needs_review = (
        overall < config.CONFIDENCE_THRESHOLD_REVIEW or
        not metadata.get('reconciliation_passed', True) or
        _has_outliers(transaction, metadata)
    )
    
    return ConfidenceScore(
        overall=overall,
        needs_review=needs_review,
        extraction_score=extraction_score,
        normalization_score=normalization_score,
        reconciliation_score=reconciliation_score,
        factors=factors,
        penalties=[p['reason'] for p in penalties]
    )


def _calculate_normalization_score(transaction: CanonicalTransaction) -> float:
    """
    Calculate score based on data normalization quality.
    
    Args:
        transaction: Canonical transaction
    
    Returns:
        Normalization score (0.0 - 1.0)
    """
    score = 1.0
    
    # Check for required fields
    if not transaction.description or not transaction.description.strip():
        score *= 0.5
    
    if not transaction.account_id or not transaction.account_id.strip():
        score *= 0.7
    
    # Check currency
    if transaction.currency and len(transaction.currency) == 3:
        score *= 1.0  # Valid ISO currency
    else:
        score *= 0.9
    
    # Check amount sanity
    try:
        amount = abs(float(transaction.amount))
        if amount == 0:
            score *= 0.1  # Zero amounts are suspicious
        elif amount > 1000000:  # > $1M
            score *= 0.95  # Large amounts slightly penalized
    except (ValueError, TypeError):
        score *= 0.5
    
    # Check description quality
    desc_len = len(transaction.description.strip()) if transaction.description else 0
    if desc_len < 5:
        score *= 0.8  # Very short descriptions
    elif desc_len > 200:
        score *= 0.95  # Very long descriptions (might be garbled)
    
    return max(0.0, min(1.0, score))


def _calculate_penalties(transaction: CanonicalTransaction, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate confidence penalties based on data quality issues.
    
    Args:
        transaction: Canonical transaction
        metadata: Extraction metadata
    
    Returns:
        List of penalty dictionaries
    """
    penalties = []
    
    # Missing balance
    if transaction.balance is None and metadata.get('has_balance_column', False):
        penalties.append({
            'reason': 'missing_balance',
            'amount': 0.05
        })
    
    # Missing value date
    if transaction.value_date is None and metadata.get('has_value_date_column', False):
        penalties.append({
            'reason': 'missing_value_date',
            'amount': 0.02
        })
    
    # Low OCR confidence
    ocr_confidence = metadata.get('ocr_char_confidence', 1.0)
    if ocr_confidence < 0.8:
        penalties.append({
            'reason': 'low_ocr_confidence',
            'amount': 0.10
        })
    
    # Ambiguous date format
    if metadata.get('date_format_ambiguous', False):
        penalties.append({
            'reason': 'ambiguous_date_format',
            'amount': 0.08
        })
    
    # Unknown amount polarity
    if metadata.get('amount_polarity_assumed', False):
        penalties.append({
            'reason': 'assumed_polarity',
            'amount': 0.10
        })
    
    # Unusual characters in description
    if transaction.description:
        unusual_chars = sum(1 for c in transaction.description if ord(c) > 127)
        if unusual_chars > len(transaction.description) * 0.3:  # >30% non-ASCII
            penalties.append({
                'reason': 'unusual_characters',
                'amount': 0.15
            })
    
    return penalties


def _has_outliers(transaction: CanonicalTransaction, metadata: Dict[str, Any]) -> bool:
    """
    Check if transaction appears to be an outlier.
    
    Args:
        transaction: Canonical transaction
        metadata: Extraction metadata
    
    Returns:
        True if transaction is an outlier
    """
    # Extremely large amounts
    try:
        amount = abs(float(transaction.amount))
        if amount > 10000000:  # > $10M
            return True
    except (ValueError, TypeError):
        return True
    
    # Future dates
    from datetime import date as dt_date
    today = dt_date.today()
    if transaction.post_date > today:
        return True
    
    # Very old dates (>10 years)
    from datetime import timedelta
    ten_years_ago = today - timedelta(days=365*10)
    if transaction.post_date < ten_years_ago:
        return True
    
    return False


def batch_score_confidence(
    transactions: List[CanonicalTransaction],
    extraction_method: str,
    metadata: Dict[str, Any] = None
) -> List[Tuple[CanonicalTransaction, ConfidenceScore]]:
    """
    Score confidence for a batch of transactions.
    
    Args:
        transactions: List of canonical transactions
        extraction_method: Extraction method used
        metadata: Shared metadata for all transactions
    
    Returns:
        List of (transaction, confidence_score) tuples
    """
    results = []
    
    for txn in transactions:
        # Calculate confidence for this transaction
        confidence = calculate_confidence(txn, extraction_method, metadata)
        results.append((txn, confidence))
    
    return results


def get_confidence_stats(scores: List[ConfidenceScore]) -> Dict[str, Any]:
    """
    Get aggregate statistics for confidence scores.
    
    Args:
        scores: List of confidence scores
    
    Returns:
        Statistics dictionary
    """
    if not scores:
        return {
            'count': 0,
            'avg_confidence': 0.0,
            'min_confidence': 0.0,
            'max_confidence': 0.0,
            'needs_review_count': 0,
            'needs_review_percent': 0.0,
        }
    
    confidences = [s.overall for s in scores]
    needs_review = sum(1 for s in scores if s.needs_review)
    
    return {
        'count': len(scores),
        'avg_confidence': sum(confidences) / len(confidences),
        'min_confidence': min(confidences),
        'max_confidence': max(confidences),
        'needs_review_count': needs_review,
        'needs_review_percent': (needs_review / len(scores) * 100) if scores else 0.0,
    }


def adjust_confidence_thresholds(
    historical_accuracy: float,
    target_review_rate: float = 0.15
) -> float:
    """
    Dynamically adjust confidence threshold based on historical accuracy.
    
    Args:
        historical_accuracy: Accuracy rate from past reviews (0.0-1.0)
        target_review_rate: Target percentage of transactions to review (0.0-1.0)
    
    Returns:
        Adjusted confidence threshold
    """
    base_threshold = config.CONFIDENCE_THRESHOLD_REVIEW
    
    # If accuracy is high, can lower threshold (review less)
    if historical_accuracy > 0.95:
        return max(base_threshold - 0.05, 0.75)
    
    # If accuracy is low, raise threshold (review more)
    elif historical_accuracy < 0.85:
        return min(base_threshold + 0.10, 0.95)
    
    return base_threshold



