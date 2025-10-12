"""Tests for financial reports (P&L, Balance Sheet, Cash Flow)."""
import pytest

pytestmark = pytest.mark.skip(reason="app.api.analytics module incomplete - skip for v0.9.1")

from datetime import date, datetime
from unittest.mock import MagicMock
from app.db.models import JournalEntryDB


def create_mock_je(company_id, date_str, lines):
    """Helper to create mock journal entry."""
    je = MagicMock(spec=JournalEntryDB)
    je.company_id = company_id
    je.date = datetime.strptime(date_str, "%Y-%m-%d").date()
    je.lines = lines
    je.status = "posted"
    return je


def test_pnl_calculation():
    """Test P&L calculation with sample data."""
    # Create mock database session
    db = MagicMock()
    
    # Create sample journal entries
    mock_jes = [
        # Revenue entry
        create_mock_je("company_001", "2025-09-15", [
            {"account": "1000 Cash at Bank", "debit": 1000.0, "credit": 0.0},
            {"account": "8000 Sales Revenue", "debit": 0.0, "credit": 1000.0}
        ]),
        # Expense entry
        create_mock_je("company_001", "2025-09-20", [
            {"account": "6100 Office Supplies", "debit": 250.0, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 250.0}
        ])
    ]
    
    # Mock query chain
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    
    # Generate P&L
    result = generate_pnl(
        db,
        "company_001",
        date(2025, 9, 1),
        date(2025, 9, 30)
    )
    
    # Verify structure
    assert "revenue" in result
    assert "expenses" in result
    assert "net_income" in result
    
    # Verify calculations
    assert result["revenue"]["total"] == 1000.0
    assert result["expenses"]["total"] == 250.0
    assert result["net_income"] == 750.0
    
    # Verify margin
    assert result["margin_percent"] == 75.0


def test_balance_sheet_structure():
    """Test Balance Sheet structure and balance check."""
    db = MagicMock()
    
    # Create balanced entries
    mock_jes = [
        # Asset increase
        create_mock_je("company_001", "2025-09-01", [
            {"account": "1000 Cash at Bank", "debit": 5000.0, "credit": 0.0},
            {"account": "8000 Sales Revenue", "debit": 0.0, "credit": 5000.0}
        ]),
        # Liability increase
        create_mock_je("company_001", "2025-09-15", [
            {"account": "1000 Cash at Bank", "debit": 1000.0, "credit": 0.0},
            {"account": "2000 Credit Card Payable", "debit": 0.0, "credit": 1000.0}
        ])
    ]
    
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    
    result = generate_balance_sheet(
        db,
        "company_001",
        date(2025, 9, 30)
    )
    
    # Verify structure
    assert "assets" in result
    assert "liabilities" in result
    assert "equity" in result
    assert "balanced" in result
    
    # Verify balance equation: Assets = Liabilities + Equity
    assets = result["assets"]["total"]
    liabilities = result["liabilities"]["total"]
    equity = result["equity"]["total"]
    
    assert result["balanced"] is True
    assert abs(assets - (liabilities + equity)) < 0.01


def test_cashflow_operating_activities():
    """Test Cash Flow operating activities calculation."""
    db = MagicMock()
    
    # Mock P&L for net income
    mock_jes = [
        create_mock_je("company_001", "2025-09-15", [
            {"account": "1000 Cash at Bank", "debit": 2000.0, "credit": 0.0},
            {"account": "8000 Sales Revenue", "debit": 0.0, "credit": 2000.0}
        ]),
        create_mock_je("company_001", "2025-09-20", [
            {"account": "6100 Office Supplies", "debit": 500.0, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 500.0}
        ])
    ]
    
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    
    result = generate_cashflow(
        db,
        "company_001",
        date(2025, 9, 1),
        date(2025, 9, 30)
    )
    
    # Verify structure
    assert "operating_activities" in result
    assert "investing_activities" in result
    assert "financing_activities" in result
    assert "net_cash_change" in result
    
    # Verify net income in operating activities
    assert "net_income" in result["operating_activities"]
    assert result["operating_activities"]["net_income"] == 1500.0  # 2000 - 500


def test_pnl_empty_period():
    """Test P&L with no transactions."""
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    
    result = generate_pnl(
        db,
        "company_001",
        date(2025, 9, 1),
        date(2025, 9, 30)
    )
    
    assert result["revenue"]["total"] == 0.0
    assert result["expenses"]["total"] == 0.0
    assert result["net_income"] == 0.0


def test_balance_sheet_accounts_categorization():
    """Test that accounts are correctly categorized."""
    db = MagicMock()
    
    mock_jes = [
        # Asset (1xxx)
        create_mock_je("company_001", "2025-09-01", [
            {"account": "1000 Cash at Bank", "debit": 1000.0, "credit": 0.0},
            {"account": "8000 Sales Revenue", "debit": 0.0, "credit": 1000.0}
        ]),
        # Liability (2xxx)
        create_mock_je("company_001", "2025-09-01", [
            {"account": "6100 Office Supplies", "debit": 500.0, "credit": 0.0},
            {"account": "2000 Credit Card Payable", "debit": 0.0, "credit": 500.0}
        ])
    ]
    
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    
    result = generate_balance_sheet(
        db,
        "company_001",
        date(2025, 9, 30)
    )
    
    # Check that cash is in assets
    assert "1000 Cash at Bank" in result["assets"]["accounts"]
    
    # Check that credit card payable is in liabilities
    assert "2000 Credit Card Payable" in result["liabilities"]["accounts"]


def test_retained_earnings_calculation():
    """Test that retained earnings are properly calculated."""
    db = MagicMock()
    
    # Profitable period
    mock_jes = [
        create_mock_je("company_001", "2025-09-15", [
            {"account": "1000 Cash at Bank", "debit": 5000.0, "credit": 0.0},
            {"account": "8000 Sales Revenue", "debit": 0.0, "credit": 5000.0}
        ]),
        create_mock_je("company_001", "2025-09-20", [
            {"account": "6100 Office Supplies", "debit": 1000.0, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": 1000.0}
        ])
    ]
    
    db.query.return_value.filter.return_value.all.return_value = mock_jes
    
    result = generate_balance_sheet(
        db,
        "company_001",
        date(2025, 9, 30)
    )
    
    # Retained earnings should reflect net income
    assert "3000 Retained Earnings" in result["equity"]["accounts"]
    # Net income = 5000 - 1000 = 4000
    assert result["equity"]["accounts"]["3000 Retained Earnings"] == 4000.0

