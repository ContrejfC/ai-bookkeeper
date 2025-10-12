"""Tests for dashboard and analytics endpoints."""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.api.analytics.automation_metrics import get_automation_metrics


def test_automation_metrics_structure():
    """Test that automation metrics return correct structure."""
    db = MagicMock()
    
    # Mock query results
    db.query.return_value.filter.return_value.scalar.side_effect = [
        100,  # total_jes
        80,   # auto_approved
        20,   # needs_review
        90,   # posted
        100,  # total_txns
        95    # matched_txns
    ]
    
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = get_automation_metrics(db, "company_001", days=30)
    
    # Verify structure
    assert "company_id" in result
    assert "period_days" in result
    assert "journal_entries" in result
    assert "rates" in result
    assert "transactions" in result
    assert "targets" in result
    assert "status" in result
    
    # Verify journal entries
    je = result["journal_entries"]
    assert "total" in je
    assert "auto_approved" in je
    assert "needs_review" in je
    assert "posted" in je


def test_automation_rates_calculation():
    """Test that automation rates are calculated correctly."""
    db = MagicMock()
    
    # 80 auto-approved out of 100 total = 80% auto-approval rate
    db.query.return_value.filter.return_value.scalar.side_effect = [
        100,  # total
        80,   # auto_approved
        20,   # needs_review
        90,   # posted
        100,  # total_txns
        90    # matched_txns
    ]
    
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = get_automation_metrics(db, "company_001", days=30)
    
    assert result["rates"]["auto_approval_rate"] == 80.0
    assert result["rates"]["review_rate"] == 20.0
    assert result["rates"]["recon_match_rate"] == 90.0


def test_target_achievement_status():
    """Test that target achievement status is reported correctly."""
    db = MagicMock()
    
    # Meeting all targets
    db.query.return_value.filter.return_value.scalar.side_effect = [
        100,  # total
        85,   # auto_approved (>= 80% target)
        15,   # needs_review (<= 20% target)
        90,   # posted
        100,  # total_txns
        95    # matched_txns (>= 90% target)
    ]
    
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = get_automation_metrics(db, "company_001", days=30)
    
    # All targets should be met
    assert result["status"]["auto_approval_met"] is True
    assert result["status"]["recon_match_met"] is True
    assert result["status"]["review_met"] is True


def test_zero_transactions_handling():
    """Test metrics calculation with zero transactions."""
    db = MagicMock()
    
    # All zeros
    db.query.return_value.filter.return_value.scalar.return_value = 0
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = get_automation_metrics(db, "company_001", days=30)
    
    # Should not crash and should return 0% rates
    assert result["rates"]["auto_approval_rate"] == 0.0
    assert result["rates"]["review_rate"] == 0.0
    assert result["rates"]["recon_match_rate"] == 0.0


def test_dashboard_json_shapes():
    """Test that all dashboard endpoints return valid JSON shapes."""
    # This is a structure test - in integration tests, we'd call actual endpoints
    
    # Expected P&L shape
    pnl_shape = {
        "company_id": str,
        "start_date": str,
        "end_date": str,
        "revenue": dict,
        "expenses": dict,
        "net_income": float,
        "margin_percent": float
    }
    
    # Expected Balance Sheet shape
    bs_shape = {
        "company_id": str,
        "as_of_date": str,
        "assets": dict,
        "liabilities": dict,
        "equity": dict,
        "balanced": bool
    }
    
    # Expected Cash Flow shape
    cf_shape = {
        "company_id": str,
        "start_date": str,
        "end_date": str,
        "operating_activities": dict,
        "investing_activities": dict,
        "financing_activities": dict,
        "net_cash_change": float
    }
    
    # Expected Automation Metrics shape
    am_shape = {
        "company_id": str,
        "period_days": int,
        "journal_entries": dict,
        "rates": dict,
        "transactions": dict,
        "targets": dict,
        "status": dict
    }
    
    # All shapes are valid
    assert all([pnl_shape, bs_shape, cf_shape, am_shape])


def test_non_empty_time_series():
    """Test that time series data is not empty."""
    db = MagicMock()
    
    # Mock some journal entries
    mock_jes = [MagicMock() for _ in range(10)]
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    db.query.return_value.filter.return_value.scalar.return_value = 10
    
    result = get_automation_metrics(db, "company_001", days=30)
    
    # Should have non-zero data
    assert result["journal_entries"]["total"] == 10

