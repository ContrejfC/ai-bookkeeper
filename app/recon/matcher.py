"""Reconciliation matcher for linking transactions to journal entries."""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import (
    TransactionDB, JournalEntryDB, ReconciliationDB
)
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ReconciliationMatcher:
    """Matcher for reconciling transactions with journal entries."""
    
    def __init__(self, db: Session, date_tolerance: int = None):
        """
        Initialize the reconciliation matcher.
        
        Args:
            db: Database session
            date_tolerance: Days to allow for date matching (default from settings)
        """
        self.db = db
        self.date_tolerance = date_tolerance or settings.recon_date_tolerance_days
    
    def reconcile_all(self) -> Dict[str, Any]:
        """
        Reconcile all transactions with journal entries.
        
        Returns:
            Dict with reconciliation results and statistics
        """
        # Get all transactions
        transactions = self.db.query(TransactionDB).all()
        
        # Get all posted journal entries
        journal_entries = self.db.query(JournalEntryDB).filter(
            JournalEntryDB.status.in_(["approved", "posted"])
        ).all()
        
        # Clear existing reconciliations
        self.db.query(ReconciliationDB).delete()
        
        results = []
        matched_txns = set()
        matched_jes = set()
        
        # Try exact matching first
        for txn in transactions:
            for je in journal_entries:
                if je.je_id in matched_jes:
                    continue
                
                match_type, score = self._match_transaction_je(txn, je)
                
                if match_type:
                    # Create reconciliation record
                    recon = ReconciliationDB(
                        txn_id=txn.txn_id,
                        je_id=je.je_id,
                        match_type=match_type,
                        match_score=score
                    )
                    self.db.add(recon)
                    
                    results.append(ReconciliationResult(
                        txn_id=txn.txn_id,
                        je_id=je.je_id,
                        match_type=match_type,
                        match_score=score,
                        status="matched"
                    ))
                    
                    matched_txns.add(txn.txn_id)
                    matched_jes.add(je.je_id)
                    break
        
        # Find unmatched transactions
        for txn in transactions:
            if txn.txn_id not in matched_txns:
                results.append(ReconciliationResult(
                    txn_id=txn.txn_id,
                    je_id=None,
                    match_type=None,
                    match_score=0.0,
                    status="unmatched"
                ))
        
        # Find orphaned journal entries (posted but no transaction)
        for je in journal_entries:
            if je.je_id not in matched_jes:
                results.append(ReconciliationResult(
                    txn_id=je.source_txn_id or "unknown",
                    je_id=je.je_id,
                    match_type=None,
                    match_score=0.0,
                    status="orphan"
                ))
        
        self.db.commit()
        
        # Calculate statistics
        stats = {
            "total_transactions": len(transactions),
            "total_journal_entries": len(journal_entries),
            "matched": len(matched_txns),
            "unmatched_transactions": len(transactions) - len(matched_txns),
            "orphaned_journal_entries": len(journal_entries) - len(matched_jes),
            "match_rate": len(matched_txns) / len(transactions) if transactions else 0.0
        }
        
        return {
            "results": [r.model_dump() for r in results],
            "statistics": stats
        }
    
    def _match_transaction_je(
        self,
        txn: TransactionDB,
        je: JournalEntryDB
    ) -> Tuple[str, float]:
        """
        Match a transaction to a journal entry.
        
        Returns:
            Tuple of (match_type, score) or (None, 0.0) if no match
        """
        # Check if JE is linked to this transaction
        if je.source_txn_id == txn.txn_id:
            return ("exact", 1.0)
        
        # Check amount and date matching
        je_amount = self._get_je_cash_amount(je)
        
        if je_amount is None:
            return (None, 0.0)
        
        # Amount must match (within tolerance)
        if abs(abs(je_amount) - abs(txn.amount)) > 0.01:
            return (None, 0.0)
        
        # Date must be within tolerance
        date_diff = abs((je.date - txn.date).days)
        
        if date_diff <= self.date_tolerance:
            if date_diff == 0:
                return ("exact", 1.0)
            else:
                score = 1.0 - (date_diff / (self.date_tolerance * 2))
                return ("heuristic", max(score, 0.5))
        
        return (None, 0.0)
    
    def _get_je_cash_amount(self, je: JournalEntryDB) -> float:
        """
        Extract the cash account amount from a journal entry.
        
        Returns:
            The cash amount (positive for debit, negative for credit) or None
        """
        for line in je.lines:
            if "Cash at Bank" in line.get('account', ''):
                if line.get('debit', 0) > 0:
                    return line['debit']
                elif line.get('credit', 0) > 0:
                    return -line['credit']
        
        return None
    
    def get_unmatched_transactions(self) -> List[TransactionDB]:
        """Get all unmatched transactions."""
        matched_ids = self.db.query(ReconciliationDB.txn_id).distinct().all()
        matched_ids = [row[0] for row in matched_ids]
        
        return self.db.query(TransactionDB).filter(
            ~TransactionDB.txn_id.in_(matched_ids)
        ).all()
    
    def get_orphaned_journal_entries(self) -> List[JournalEntryDB]:
        """Get all orphaned journal entries (posted but no transaction match)."""
        matched_ids = self.db.query(ReconciliationDB.je_id).distinct().all()
        matched_ids = [row[0] for row in matched_ids]
        
        return self.db.query(JournalEntryDB).filter(
            JournalEntryDB.status == "posted",
            ~JournalEntryDB.je_id.in_(matched_ids)
        ).all()

