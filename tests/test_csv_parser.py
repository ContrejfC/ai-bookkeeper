"""Tests for CSV parser."""
import pytest
from pathlib import Path
from app.ingest.csv_parser import parse_csv_statement, extract_counterparty


def test_parse_sample_csv():
    """Test parsing the sample CSV fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_bank_statement.csv"
    
    transactions = parse_csv_statement(str(fixture_path))
    
    assert len(transactions) > 0
    assert transactions[0].txn_id.startswith("txn_")
    assert transactions[0].currency == "USD"
    
    # Check that amounts are parsed correctly
    assert isinstance(transactions[0].amount, float)
    
    # Check date format
    assert "-" in transactions[0].date  # Should be YYYY-MM-DD


def test_extract_counterparty():
    """Test counterparty extraction from descriptions."""
    # Test with common prefixes (removes DEBIT, CARD, etc.)
    assert extract_counterparty("DEBIT CARD PURCHASE AMAZON") == "CARD PURCHASE AMAZON"
    
    # ACH and TRANSFER are both removed, leaving PAYROLL
    assert extract_counterparty("ACH TRANSFER PAYROLL") == "PAYROLL"
    
    # Test simple case
    assert extract_counterparty("STARBUCKS STORE 1234") == "STARBUCKS STORE 1234"
    
    # Test empty
    assert extract_counterparty("") == "Unknown"

