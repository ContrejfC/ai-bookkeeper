"""
Test Standards Parsers - Roundtrip Validation
=============================================

Tests that all standards parsers correctly process fixtures and produce
canonical transactions with proper reconciliation, currency, and signs.
"""

import pytest
from pathlib import Path
from decimal import Decimal

from app.ingestion.standards import parse_camt, parse_mt940, parse_bai2, parse_ofx


# Fixtures paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "standards"


class TestCAMTParsing:
    """Test CAMT (ISO 20022) parser."""
    
    def test_camt053_parses(self):
        """Test CAMT.053 parsing."""
        file_path = FIXTURES_DIR / "camt053_min.xml"
        transactions = parse_camt(file_path)
        
        assert len(transactions) > 0, "Should parse at least one transaction"
        assert len(transactions) == 5, f"Expected 5 transactions, got {len(transactions)}"
    
    def test_camt053_amounts(self):
        """Test CAMT.053 amounts are correct."""
        file_path = FIXTURES_DIR / "camt053_min.xml"
        transactions = parse_camt(file_path)
        
        # Check first transaction (debit of 500)
        assert transactions[0].amount == -500.00, "First transaction should be -500"
        
        # Check second transaction (credit of 2500)
        assert transactions[1].amount == 2500.00, "Second transaction should be +2500"
    
    def test_camt053_currency(self):
        """Test CAMT.053 currency detection."""
        file_path = FIXTURES_DIR / "camt053_min.xml"
        transactions = parse_camt(file_path)
        
        for txn in transactions:
            assert txn.currency == "USD", f"Expected USD, got {txn.currency}"
    
    def test_camt053_dates(self):
        """Test CAMT.053 date parsing."""
        file_path = FIXTURES_DIR / "camt053_min.xml"
        transactions = parse_camt(file_path)
        
        for txn in transactions:
            assert txn.post_date is not None, "All transactions should have dates"
    
    def test_camt053_reconciliation(self):
        """Test CAMT.053 reconciliation."""
        file_path = FIXTURES_DIR / "camt053_min.xml"
        transactions = parse_camt(file_path)
        
        # Opening balance: 10000
        # Transactions: -500, +2500, -150, -800, +1200 = +2250
        # Expected closing: 12250
        
        net_change = sum(t.amount for t in transactions)
        assert abs(net_change - 2250.00) < 0.01, f"Net change should be 2250, got {net_change}"
    
    def test_camt054_parses(self):
        """Test CAMT.054 parsing."""
        file_path = FIXTURES_DIR / "camt054_min.xml"
        transactions = parse_camt(file_path)
        
        assert len(transactions) == 2, f"Expected 2 transactions, got {len(transactions)}"
        assert transactions[0].currency == "EUR", "Should detect EUR currency"


class TestMT940Parsing:
    """Test MT940 (SWIFT) parser."""
    
    def test_mt940_parses(self):
        """Test MT940 parsing."""
        file_path = FIXTURES_DIR / "mt940_min.txt"
        transactions = parse_mt940(file_path)
        
        assert len(transactions) == 5, f"Expected 5 transactions, got {len(transactions)}"
    
    def test_mt940_amounts(self):
        """Test MT940 amounts and signs."""
        file_path = FIXTURES_DIR / "mt940_min.txt"
        transactions = parse_mt940(file_path)
        
        # First transaction should be debit (negative)
        assert transactions[0].amount < 0, "First transaction should be negative"
        
        # Second transaction should be credit (positive)
        assert transactions[1].amount > 0, "Second transaction should be positive"
    
    def test_mt940_reconciliation(self):
        """Test MT940 reconciliation."""
        file_path = FIXTURES_DIR / "mt940_min.txt"
        transactions = parse_mt940(file_path)
        
        # Should match CAMT test: net change of 2250
        net_change = sum(t.amount for t in transactions)
        assert abs(net_change - 2250.00) < 0.01, f"Net change should be 2250, got {net_change}"


class TestBAI2Parsing:
    """Test BAI2 parser."""
    
    def test_bai2_parses(self):
        """Test BAI2 parsing."""
        file_path = FIXTURES_DIR / "bai2_min.txt"
        transactions = parse_bai2(file_path)
        
        assert len(transactions) == 5, f"Expected 5 transactions, got {len(transactions)}"
    
    def test_bai2_amounts_in_cents(self):
        """Test BAI2 amounts are converted from cents."""
        file_path = FIXTURES_DIR / "bai2_min.txt"
        transactions = parse_bai2(file_path)
        
        # BAI2 stores amounts in cents (50000 = $500.00)
        # First transaction: type 165 (debit), amount 50000 cents = -500.00
        assert transactions[0].amount == -500.00, f"Expected -500.00, got {transactions[0].amount}"


class TestOFXParsing:
    """Test OFX parser."""
    
    def test_ofx_parses(self):
        """Test OFX parsing."""
        file_path = FIXTURES_DIR / "ofx_min.ofx"
        transactions = parse_ofx(file_path)
        
        assert len(transactions) == 5, f"Expected 5 transactions, got {len(transactions)}"
    
    def test_ofx_amounts(self):
        """Test OFX amounts."""
        file_path = FIXTURES_DIR / "ofx_min.ofx"
        transactions = parse_ofx(file_path)
        
        # First transaction: DEBIT of -500.00
        assert transactions[0].amount == -500.00, "First transaction should be -500"
        
        # Second transaction: CREDIT of 2500.00
        assert transactions[1].amount == 2500.00, "Second transaction should be +2500"
    
    def test_ofx_fitid(self):
        """Test OFX transaction IDs."""
        file_path = FIXTURES_DIR / "ofx_min.ofx"
        transactions = parse_ofx(file_path)
        
        # All transactions should have references (FITID)
        for txn in transactions:
            assert txn.reference is not None, "All OFX transactions should have FITID"
            assert txn.reference.startswith("TXN"), f"Expected TXN prefix, got {txn.reference}"


class TestCrossFormatConsistency:
    """Test that different formats produce consistent results for same data."""
    
    def test_all_formats_same_net_change(self):
        """Test all formats produce the same net transaction amount."""
        camt_txns = parse_camt(FIXTURES_DIR / "camt053_min.xml")
        mt940_txns = parse_mt940(FIXTURES_DIR / "mt940_min.txt")
        bai2_txns = parse_bai2(FIXTURES_DIR / "bai2_min.txt")
        ofx_txns = parse_ofx(FIXTURES_DIR / "ofx_min.ofx")
        
        camt_net = sum(t.amount for t in camt_txns)
        mt940_net = sum(t.amount for t in mt940_txns)
        bai2_net = sum(t.amount for t in bai2_txns)
        ofx_net = sum(t.amount for t in ofx_txns)
        
        # All should have same net change (within rounding)
        assert abs(camt_net - mt940_net) < 0.01, "CAMT and MT940 should match"
        assert abs(camt_net - bai2_net) < 0.01, "CAMT and BAI2 should match"
        assert abs(camt_net - ofx_net) < 0.01, "CAMT and OFX should match"
    
    def test_all_formats_same_row_count(self):
        """Test all formats produce same number of transactions."""
        camt_txns = parse_camt(FIXTURES_DIR / "camt053_min.xml")
        mt940_txns = parse_mt940(FIXTURES_DIR / "mt940_min.txt")
        bai2_txns = parse_bai2(FIXTURES_DIR / "bai2_min.txt")
        ofx_txns = parse_ofx(FIXTURES_DIR / "ofx_min.ofx")
        
        assert len(camt_txns) == len(mt940_txns) == len(bai2_txns) == len(ofx_txns) == 5, \
            "All formats should produce 5 transactions"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



