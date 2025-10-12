"""Tests for reconciliation functionality."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from app.db.models import TransactionDB, JournalEntryDB
from app.recon.matcher import ReconciliationMatcher


def test_exact_match():
    """Test exact matching of transaction to journal entry."""
    # Create mock DB session
    db = MagicMock()
    
    # Create test transaction
    txn = TransactionDB(
        txn_id="txn_001",
        date=datetime(2025, 10, 1).date(),
        amount=-100.00,
        currency="USD",
        description="Test vendor",
        counterparty="Test Vendor"
    )
    
    # Create matching journal entry
    je = JournalEntryDB(
        je_id="je_001",
        date=datetime(2025, 10, 1).date(),
        lines=[
            {"account": "6100 Office Supplies", "debit": 100.00, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 100.00}
        ],
        source_txn_id="txn_001",
        status="posted"
    )
    
    matcher = ReconciliationMatcher(db)
    match_type, score = matcher._match_transaction_je(txn, je)
    
    assert match_type == "exact"
    assert score == 1.0


def test_date_tolerance_match():
    """Test matching with date tolerance."""
    db = MagicMock()
    
    # Create test transaction
    txn = TransactionDB(
        txn_id="txn_002",
        date=datetime(2025, 10, 1).date(),
        amount=-100.00,
        currency="USD",
        description="Test vendor",
        counterparty="Test Vendor"
    )
    
    # Create journal entry with slightly different date
    je = JournalEntryDB(
        je_id="je_002",
        date=datetime(2025, 10, 3).date(),  # 2 days later
        lines=[
            {"account": "6100 Office Supplies", "debit": 100.00, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 100.00}
        ],
        source_txn_id="txn_999",  # Different source
        status="posted"
    )
    
    matcher = ReconciliationMatcher(db, date_tolerance=3)
    match_type, score = matcher._match_transaction_je(txn, je)
    
    assert match_type == "heuristic"
    assert 0.5 <= score < 1.0


def test_no_match_amount_mismatch():
    """Test that entries with different amounts don't match."""
    db = MagicMock()
    
    # Create test transaction
    txn = TransactionDB(
        txn_id="txn_003",
        date=datetime(2025, 10, 1).date(),
        amount=-100.00,
        currency="USD",
        description="Test vendor",
        counterparty="Test Vendor"
    )
    
    # Create journal entry with different amount
    je = JournalEntryDB(
        je_id="je_003",
        date=datetime(2025, 10, 1).date(),
        lines=[
            {"account": "6100 Office Supplies", "debit": 150.00, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 150.00}
        ],
        source_txn_id="txn_999",
        status="posted"
    )
    
    matcher = ReconciliationMatcher(db)
    match_type, score = matcher._match_transaction_je(txn, je)
    
    assert match_type is None
    assert score == 0.0


def test_no_match_date_out_of_tolerance():
    """Test that entries outside date tolerance don't match."""
    db = MagicMock()
    
    # Create test transaction
    txn = TransactionDB(
        txn_id="txn_004",
        date=datetime(2025, 10, 1).date(),
        amount=-100.00,
        currency="USD",
        description="Test vendor",
        counterparty="Test Vendor"
    )
    
    # Create journal entry with date far in future
    je = JournalEntryDB(
        je_id="je_004",
        date=datetime(2025, 10, 10).date(),  # 9 days later
        lines=[
            {"account": "6100 Office Supplies", "debit": 100.00, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 100.00}
        ],
        source_txn_id="txn_999",
        status="posted"
    )
    
    matcher = ReconciliationMatcher(db, date_tolerance=3)
    match_type, score = matcher._match_transaction_je(txn, je)
    
    assert match_type is None
    assert score == 0.0

