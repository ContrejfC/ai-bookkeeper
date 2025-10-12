#!/usr/bin/env python3
"""
Fixture Sanity Tests for Stage A (Sprint 9).

Validates:
- 1,200 rows per tenant
- Required headers present
- Date span ≈ 12 months
- Vendor distribution long-tail (top vendor < 20%)
"""
import pytest
import csv
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter


FIXTURES_DIR = Path(__file__).parent / "fixtures"
REQUIRED_HEADERS = [
    "company_id", "company_name", "txn_id", "date", "amount",
    "description", "counterparty", "currency", "suggested_account",
    "confidence", "source_type", "source_name"
]


class TestFixtureSanity:
    """Sanity tests for Stage A fixtures."""
    
    def test_tenant_alpha_row_count(self):
        """Verify Tenant Alpha has exactly 1,200 transactions."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1200, f"Expected 1,200 rows, got {len(rows)}"
    
    def test_tenant_beta_row_count(self):
        """Verify Tenant Beta has exactly 1,200 transactions."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1200, f"Expected 1,200 rows, got {len(rows)}"
    
    def test_alpha_headers(self):
        """Verify Tenant Alpha has all required headers."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        for required_header in REQUIRED_HEADERS:
            assert required_header in headers, f"Missing header: {required_header}"
    
    def test_beta_headers(self):
        """Verify Tenant Beta has all required headers."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        for required_header in REQUIRED_HEADERS:
            assert required_header in headers, f"Missing header: {required_header}"
    
    def test_alpha_date_span(self):
        """Verify Tenant Alpha date span is approximately 12 months."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            dates = [datetime.strptime(row["date"], "%Y-%m-%d") for row in reader]
        
        min_date = min(dates)
        max_date = max(dates)
        span_days = (max_date - min_date).days
        
        # Allow some flexibility (300-400 days)
        assert 300 <= span_days <= 400, f"Date span {span_days} days not ≈ 12 months (300-400 days)"
    
    def test_beta_date_span(self):
        """Verify Tenant Beta date span is approximately 12 months."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            dates = [datetime.strptime(row["date"], "%Y-%m-%d") for row in reader]
        
        min_date = min(dates)
        max_date = max(dates)
        span_days = (max_date - min_date).days
        
        # Allow some flexibility (300-400 days)
        assert 300 <= span_days <= 400, f"Date span {span_days} days not ≈ 12 months (300-400 days)"
    
    def test_alpha_vendor_distribution_longtail(self):
        """Verify Tenant Alpha vendor distribution is long-tail (top vendor < 20%)."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            vendors = [row["counterparty"] for row in reader]
        
        vendor_counts = Counter(vendors)
        total_txns = len(vendors)
        top_vendor_count = vendor_counts.most_common(1)[0][1]
        top_vendor_pct = (top_vendor_count / total_txns) * 100
        
        assert top_vendor_pct < 20, f"Top vendor has {top_vendor_pct:.1f}% (should be < 20% for long-tail)"
    
    def test_beta_vendor_distribution_longtail(self):
        """Verify Tenant Beta vendor distribution is long-tail (top vendor < 20%)."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            vendors = [row["counterparty"] for row in reader]
        
        vendor_counts = Counter(vendors)
        total_txns = len(vendors)
        top_vendor_count = vendor_counts.most_common(1)[0][1]
        top_vendor_pct = (top_vendor_count / total_txns) * 100
        
        assert top_vendor_pct < 20, f"Top vendor has {top_vendor_pct:.1f}% (should be < 20% for long-tail)"
    
    def test_alpha_company_id_consistent(self):
        """Verify all rows have consistent company_id."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            company_ids = set(row["company_id"] for row in reader)
        
        assert len(company_ids) == 1, f"Expected 1 company_id, found {len(company_ids)}"
        assert "fixture_alpha" in company_ids, "company_id should be 'fixture_alpha'"
    
    def test_beta_company_id_consistent(self):
        """Verify all rows have consistent company_id."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            company_ids = set(row["company_id"] for row in reader)
        
        assert len(company_ids) == 1, f"Expected 1 company_id, found {len(company_ids)}"
        assert "fixture_beta" in company_ids, "company_id should be 'fixture_beta'"
    
    def test_alpha_amounts_numeric(self):
        """Verify all amounts are valid numbers."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                try:
                    amount = float(row["amount"])
                    assert -100000 < amount < 100000, f"Suspiciously large amount: {amount}"
                except ValueError:
                    pytest.fail(f"Row {idx}: Invalid amount '{row['amount']}'")
    
    def test_beta_amounts_numeric(self):
        """Verify all amounts are valid numbers."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                try:
                    amount = float(row["amount"])
                    assert -100000 < amount < 100000, f"Suspiciously large amount: {amount}"
                except ValueError:
                    pytest.fail(f"Row {idx}: Invalid amount '{row['amount']}'")
    
    def test_fixture_seeds_documentation_exists(self):
        """Verify FIXTURE_SEEDS.md exists and contains seed info."""
        seeds_path = FIXTURES_DIR / "FIXTURE_SEEDS.md"
        assert seeds_path.exists(), f"FIXTURE_SEEDS.md not found: {seeds_path}"
        
        with open(seeds_path, "r") as f:
            content = f.read()
        
        assert "1001" in content, "Seed 1001 (Tenant Alpha) not documented"
        assert "2002" in content, "Seed 2002 (Tenant Beta) not documented"
        assert "fixture_alpha" in content, "fixture_alpha not documented"
        assert "fixture_beta" in content, "fixture_beta not documented"


class TestFixtureStatistics:
    """Statistical tests for fixture quality."""
    
    def test_alpha_vendor_count(self):
        """Verify Tenant Alpha has a reasonable number of vendors."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            vendors = set(row["counterparty"] for row in reader)
        
        # Should have 30-100 unique vendors for realism
        assert 30 <= len(vendors) <= 100, f"Expected 30-100 vendors, got {len(vendors)}"
    
    def test_beta_vendor_count(self):
        """Verify Tenant Beta has a reasonable number of vendors."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            vendors = set(row["counterparty"] for row in reader)
        
        # Should have 30-100 unique vendors for realism
        assert 30 <= len(vendors) <= 100, f"Expected 30-100 vendors, got {len(vendors)}"
    
    def test_alpha_account_diversity(self):
        """Verify Tenant Alpha uses diverse account categories."""
        fixture_path = FIXTURES_DIR / "tenant_alpha_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            accounts = set(row["suggested_account"] for row in reader)
        
        # Should have at least 10 different accounts
        assert len(accounts) >= 10, f"Expected >= 10 accounts, got {len(accounts)}"
    
    def test_beta_account_diversity(self):
        """Verify Tenant Beta uses diverse account categories."""
        fixture_path = FIXTURES_DIR / "tenant_beta_txns.csv"
        
        with open(fixture_path, "r") as f:
            reader = csv.DictReader(f)
            accounts = set(row["suggested_account"] for row in reader)
        
        # Should have at least 10 different accounts
        assert len(accounts) >= 10, f"Expected >= 10 accounts, got {len(accounts)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

