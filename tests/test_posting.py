"""Tests for journal entry posting functionality."""
import pytest
from app.db.models import Transaction, JournalEntry, JournalEntryLine


def test_journal_entry_balance():
    """Test that journal entries must be balanced."""
    # Balanced entry
    je = JournalEntry(
        je_id="test_je_1",
        date="2025-10-01",
        lines=[
            JournalEntryLine(account="6100 Office Supplies", debit=100.00, credit=0.0),
            JournalEntryLine(account="1000 Cash at Bank", debit=0.0, credit=100.00)
        ],
        source_txn_id="test_txn_1",
        memo="Test entry",
        confidence=1.0,
        status="proposed"
    )
    
    assert je.is_balanced() is True
    assert je.get_balance_diff() == 0.0


def test_journal_entry_unbalanced():
    """Test detection of unbalanced journal entries."""
    # Unbalanced entry
    je = JournalEntry(
        je_id="test_je_2",
        date="2025-10-01",
        lines=[
            JournalEntryLine(account="6100 Office Supplies", debit=100.00, credit=0.0),
            JournalEntryLine(account="1000 Cash at Bank", debit=0.0, credit=95.00)
        ],
        source_txn_id="test_txn_2",
        memo="Test unbalanced entry",
        confidence=0.5,
        status="proposed"
    )
    
    assert je.is_balanced() is False
    assert abs(je.get_balance_diff() - 5.00) < 0.01


def test_journal_entry_validation():
    """Test that JournalEntry validates line amounts."""
    # Try to create entry with negative amounts (should fail)
    with pytest.raises(ValueError):
        JournalEntryLine(account="Test Account", debit=-50.0, credit=0.0)


def test_transaction_date_validation():
    """Test that Transaction validates date format."""
    # Valid date
    txn = Transaction(
        txn_id="test_txn_3",
        date="2025-10-01",
        amount=100.00,
        currency="USD",
        description="Test transaction"
    )
    assert txn.date == "2025-10-01"
    
    # Invalid date format
    with pytest.raises(ValueError):
        Transaction(
            txn_id="test_txn_4",
            date="10/01/2025",  # Wrong format
            amount=100.00,
            currency="USD",
            description="Test transaction"
        )


def test_journal_entry_rounding():
    """Test that journal entries handle floating point precision correctly."""
    # Entry with potential rounding issues
    je = JournalEntry(
        je_id="test_je_3",
        date="2025-10-01",
        lines=[
            JournalEntryLine(account="6100 Office Supplies", debit=33.33, credit=0.0),
            JournalEntryLine(account="6100 Office Supplies", debit=33.33, credit=0.0),
            JournalEntryLine(account="6100 Office Supplies", debit=33.34, credit=0.0),
            JournalEntryLine(account="1000 Cash at Bank", debit=0.0, credit=100.00)
        ],
        source_txn_id="test_txn_5",
        memo="Test rounding",
        confidence=1.0,
        status="proposed"
    )
    
    assert je.is_balanced() is True

