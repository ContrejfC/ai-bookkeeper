"""
Document→Transaction Reconciliation

Fuzzy matching of OCR-extracted document fields to existing transactions
using vendor similarity, amount tolerance, and date windows.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def jaro_winkler_similarity(s1: str, s2: str) -> float:
    """
    Calculate Jaro-Winkler similarity between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score (0-1)
    """
    if not s1 or not s2:
        return 0.0
    
    # Use SequenceMatcher as approximation
    # (True Jaro-Winkler requires additional library)
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Calculate normalized Levenshtein similarity.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score (0-1)
    """
    if not s1 or not s2:
        return 0.0
    
    # Simple implementation
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    
    # Use SequenceMatcher
    return SequenceMatcher(None, s1, s2).ratio()


class DocumentReconciler:
    """
    Reconciles OCR-extracted documents to existing transactions.
    
    Uses fuzzy matching on vendor, amount, and date with configurable tolerances.
    """
    
    def __init__(
        self,
        amount_tolerance: float = 0.05,
        date_window_days: int = 3,
        min_vendor_similarity: float = 0.70
    ):
        """
        Initialize document reconciler.
        
        Args:
            amount_tolerance: Amount tolerance (e.g., 0.05 for ±$0.05)
            date_window_days: Date matching window (e.g., ±3 days)
            min_vendor_similarity: Minimum vendor similarity to consider
        """
        self.amount_tolerance = amount_tolerance
        self.date_window_days = date_window_days
        self.min_vendor_similarity = min_vendor_similarity
        
        logger.info(
            f"DocumentReconciler initialized: "
            f"amount_tolerance=±${amount_tolerance}, "
            f"date_window=±{date_window_days} days, "
            f"min_vendor_similarity={min_vendor_similarity}"
        )
    
    def reconcile_document(
        self,
        document_fields: Dict[str, Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        calibrator: Any = None
    ) -> Dict[str, Any]:
        """
        Reconcile document to best matching transaction.
        
        Args:
            document_fields: OCR-extracted fields with confidence scores
            transactions: List of candidate transactions
            calibrator: Optional ConfidenceCalibrator for composite scoring
            
        Returns:
            Reconciliation result with matched transaction and scores
        """
        if not transactions:
            logger.warning("No candidate transactions provided")
            return {
                "status": "no_candidates",
                "matched_transaction": None,
                "match_confidence": 0.0
            }
        
        # Extract field values
        vendor = document_fields.get('vendor', {}).get('value', '')
        amount = document_fields.get('amount', {}).get('value', 0.0)
        date_str = document_fields.get('date', {}).get('value', '')
        
        if not vendor and not amount and not date_str:
            logger.warning("No usable fields in document")
            return {
                "status": "insufficient_fields",
                "matched_transaction": None,
                "match_confidence": 0.0
            }
        
        # Parse date
        doc_date = self._parse_date(date_str) if date_str else None
        
        # Score all transactions
        matches = []
        for txn in transactions:
            score = self._compute_match_score(
                vendor, amount, doc_date,
                txn, calibrator
            )
            
            if score > 0:
                matches.append((txn, score))
        
        if not matches:
            logger.info("No matching transactions found")
            return {
                "status": "no_match",
                "matched_transaction": None,
                "match_confidence": 0.0
            }
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        best_txn, best_score = matches[0]
        
        logger.info(
            f"Best match: txn_id={best_txn.get('txn_id', 'N/A')}, "
            f"score={best_score:.3f}"
        )
        
        # Determine status
        if calibrator and hasattr(calibrator, 'should_accept_match'):
            auto_accept = calibrator.should_accept_match(best_score)
        else:
            auto_accept = best_score >= 0.88  # Default threshold
        
        status = "matched" if auto_accept else "review_required"
        
        return {
            "status": status,
            "matched_transaction": best_txn,
            "match_confidence": best_score,
            "all_candidates": [
                {
                    "txn_id": txn.get('txn_id'),
                    "score": score
                }
                for txn, score in matches[:5]  # Top 5
            ]
        }
    
    def _compute_match_score(
        self,
        doc_vendor: str,
        doc_amount: float,
        doc_date: Optional[datetime],
        transaction: Dict[str, Any],
        calibrator: Any
    ) -> float:
        """
        Compute match score for document-transaction pair.
        
        Args:
            doc_vendor: Document vendor
            doc_amount: Document amount
            doc_date: Document date
            transaction: Transaction dict
            calibrator: Optional ConfidenceCalibrator
            
        Returns:
            Composite match score (0-1)
        """
        # Vendor similarity
        txn_counterparty = transaction.get('counterparty', '')
        txn_description = transaction.get('description', '')
        
        vendor_sim_1 = jaro_winkler_similarity(doc_vendor, txn_counterparty)
        vendor_sim_2 = jaro_winkler_similarity(doc_vendor, txn_description)
        vendor_similarity = max(vendor_sim_1, vendor_sim_2)
        
        # Skip if vendor similarity too low
        if vendor_similarity < self.min_vendor_similarity:
            return 0.0
        
        # Amount match
        txn_amount = abs(transaction.get('amount', 0.0))
        amount_diff = abs(doc_amount - txn_amount)
        
        if amount_diff <= self.amount_tolerance:
            amount_match = 1.0
        elif amount_diff <= self.amount_tolerance * 3:
            # Partial match
            amount_match = 1.0 - (amount_diff / (self.amount_tolerance * 3))
        else:
            amount_match = 0.0
        
        # Date match
        if doc_date:
            txn_date_str = transaction.get('date', '')
            txn_date = self._parse_date(txn_date_str)
            
            if txn_date:
                date_diff = abs((doc_date - txn_date).days)
                
                if date_diff <= self.date_window_days:
                    date_match = 1.0 - (date_diff / (self.date_window_days * 2))
                else:
                    date_match = 0.0
            else:
                date_match = 0.5  # Unknown date
        else:
            date_match = 0.5  # Document has no date
        
        # Compute composite score
        if calibrator and hasattr(calibrator, 'compute_composite_score'):
            composite = calibrator.compute_composite_score(
                vendor_similarity, amount_match, date_match
            )
        else:
            # Default weights
            composite = (
                vendor_similarity * 0.4 +
                amount_match * 0.4 +
                date_match * 0.2
            )
        
        return composite
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        formats = [
            '%Y-%m-%d', '%Y/%m/%d',
            '%m/%d/%Y', '%m-%d-%Y',
            '%d/%m/%Y', '%d-%m-%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def update_transaction_with_document(
        self,
        transaction_id: str,
        document_id: str,
        match_confidence: float,
        db_session: Any
    ) -> bool:
        """
        Update transaction with document linkage.
        
        Args:
            transaction_id: Transaction ID
            document_id: Document ID
            match_confidence: Match confidence score
            db_session: Database session
            
        Returns:
            True if successful
        """
        try:
            from app.db.models import TransactionDB
            
            # Find transaction
            txn = db_session.query(TransactionDB).filter(
                TransactionDB.txn_id == transaction_id
            ).first()
            
            if not txn:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Update transaction
            if txn.doc_ids:
                # Append to existing doc_ids
                doc_ids = txn.doc_ids if isinstance(txn.doc_ids, list) else []
                if document_id not in doc_ids:
                    doc_ids.append(document_id)
                    txn.doc_ids = doc_ids
            else:
                txn.doc_ids = [document_id]
            
            # Store match confidence in raw metadata
            if not txn.raw:
                txn.raw = {}
            txn.raw['document_match_confidence'] = match_confidence
            txn.raw['document_verified'] = match_confidence >= 0.88
            
            db_session.commit()
            
            logger.info(
                f"Linked document {document_id} to transaction {transaction_id} "
                f"(confidence: {match_confidence:.3f})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update transaction: {e}")
            db_session.rollback()
            return False


def create_reconciler_from_settings(settings: Any) -> DocumentReconciler:
    """
    Create reconciler from settings object.
    
    Args:
        settings: Settings object
        
    Returns:
        DocumentReconciler instance
    """
    return DocumentReconciler(
        amount_tolerance=getattr(settings, 'OCR_AMOUNT_TOLERANCE', 0.05),
        date_window_days=getattr(settings, 'recon_date_tolerance_days', 3),
        min_vendor_similarity=getattr(settings, 'OCR_MIN_VENDOR_SIMILARITY', 0.70)
    )

