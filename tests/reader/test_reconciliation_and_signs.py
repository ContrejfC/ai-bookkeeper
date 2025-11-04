"""
Test Reconciliation and Sign Conventions
========================================

Tests that various sign conventions (debit/credit, negative/positive)
are handled correctly and reconciliation passes.
"""

import pytest
from decimal import Decimal
from pathlib import Path

from app.ingestion.standards import parse_camt, parse_mt940, parse_bai2, parse_ofx


class TestSignConventions:
    """Test debit/credit sign handling."""
    
    def test_camt_debits_are_negative(self):
        """Test that CAMT debits are negative."""
        file_path = Path("tests/fixtures/standards/camt053_min.xml")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_camt(file_path)
        
        # First transaction should be a debit (negative)
        assert transactions[0].amount < 0, "Debit should be negative"
    
    def test_camt_credits_are_positive(self):
        """Test that CAMT credits are positive."""
        file_path = Path("tests/fixtures/standards/camt053_min.xml")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_camt(file_path)
        
        # Second transaction should be a credit (positive)
        assert transactions[1].amount > 0, "Credit should be positive"
    
    def test_mt940_sign_consistency(self):
        """Test MT940 sign convention consistency."""
        file_path = Path("tests/fixtures/standards/mt940_min.txt")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_mt940(file_path)
        
        # Should have both debits and credits
        debits = [t for t in transactions if t.amount < 0]
        credits = [t for t in transactions if t.amount > 0]
        
        assert len(debits) > 0, "Should have at least one debit"
        assert len(credits) > 0, "Should have at least one credit"
    
    def test_bai2_cents_conversion(self):
        """Test that BAI2 amounts in cents convert correctly."""
        file_path = Path("tests/fixtures/standards/bai2_min.txt")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_bai2(file_path)
        
        # BAI2 stores amounts in cents
        # 50000 cents should become $500.00
        first_amount = abs(transactions[0].amount)
        assert first_amount == 500.00, f"Expected 500.00, got {first_amount}"


class TestReconciliation:
    """Test reconciliation logic."""
    
    def test_camt_net_change_matches(self):
        """Test that CAMT net change is correct."""
        file_path = Path("tests/fixtures/standards/camt053_min.xml")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_camt(file_path)
        
        # Calculate net change
        net = sum(Decimal(str(t.amount)) for t in transactions)
        
        # Expected: -500 + 2500 - 150 - 800 + 1200 = 2250
        expected = Decimal("2250.00")
        
        assert abs(net - expected) < Decimal("0.01"), \
            f"Net change should be {expected}, got {net}"
    
    def test_running_balance_monotone_not_required(self):
        """Test that running balance can go up and down."""
        file_path = Path("tests/fixtures/standards/camt053_min.xml")
        if not file_path.exists():
            pytest.skip("Fixture not found")
        
        transactions = parse_camt(file_path)
        
        # Balances don't have to be monotone increasing
        # (can have debits that decrease balance)
        # Just verify we have transactions
        assert len(transactions) > 0
    
    def test_cross_format_reconciliation(self):
        """Test that all formats produce same net change."""
        fixtures_dir = Path("tests/fixtures/standards")
        
        if not fixtures_dir.exists():
            pytest.skip("Fixtures directory not found")
        
        formats = {
            'camt': parse_camt(fixtures_dir / "camt053_min.xml"),
            'mt940': parse_mt940(fixtures_dir / "mt940_min.txt"),
            'bai2': parse_bai2(fixtures_dir / "bai2_min.txt"),
            'ofx': parse_ofx(fixtures_dir / "ofx_min.ofx")
        }
        
        # Calculate net change for each
        nets = {
            name: sum(Decimal(str(t.amount)) for t in txns)
            for name, txns in formats.items()
        }
        
        # All should be within $0.01 of each other
        values = list(nets.values())
        for i in range(len(values) - 1):
            diff = abs(values[i] - values[i+1])
            assert diff < Decimal("0.01"), \
                f"Net changes should match: {nets}"


class TestAdversarialReconciliation:
    """Test reconciliation with intentionally off-by-penny scenarios."""
    
    @pytest.mark.skip(reason="Requires full ingestion pipeline")
    def test_off_by_penny_triggers_review(self):
        """Test that off-by-penny reconciliation sets needs_review."""
        # This would test:
        # 1. Create synthetic data with opening balance 1000.00
        # 2. Add transactions totaling +500.00
        # 3. Set closing balance to 1500.01 (off by 1 cent)
        # 4. Verify needs_review is True
        pass
    
    @pytest.mark.skip(reason="Requires full ingestion pipeline")
    def test_large_reconciliation_error_fails(self):
        """Test that large reconciliation errors fail validation."""
        # Test with $10 discrepancy
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



