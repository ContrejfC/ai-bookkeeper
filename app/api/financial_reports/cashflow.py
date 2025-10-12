"""Cash Flow Statement generation (indirect method)."""
from datetime import date
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models import JournalEntryDB
from app.api.financial_reports.pnl import generate_pnl


def generate_cashflow(
    db: Session,
    company_id: str,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Generate Cash Flow Statement using indirect method.
    
    Operating: Net Income + adjustments + working capital changes
    Investing: Capital expenditures (placeholder)
    Financing: Loans, dividends (placeholder)
    
    Args:
        db: Database session
        company_id: Company ID filter
        start_date: Start date
        end_date: End date
        
    Returns:
        Cash flow statement
    """
    # Get P&L for net income
    pnl = generate_pnl(db, company_id, start_date, end_date)
    net_income = pnl['net_income']
    
    # Get journal entries for the period
    jes = db.query(JournalEntryDB).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.status == "posted",
            JournalEntryDB.date >= start_date,
            JournalEntryDB.date <= end_date
        )
    ).all()
    
    # Calculate adjustments (non-cash items)
    depreciation_amortization = 0.0
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            account_lower = account.lower()
            
            # Identify depreciation/amortization
            if 'depreciation' in account_lower or 'amortization' in account_lower:
                depreciation_amortization += line['debit'] - line['credit']
    
    # Working capital changes (simplified)
    # In a full implementation, we'd calculate ΔAR, ΔAP, ΔInventory, etc.
    working_capital_change = 0.0  # Placeholder
    
    # Calculate cash from operations
    cash_from_operations = (
        net_income +
        depreciation_amortization +
        working_capital_change
    )
    
    # Investing activities (placeholder)
    capital_expenditures = 0.0
    cash_from_investing = -capital_expenditures
    
    # Financing activities (placeholder)
    loan_proceeds = 0.0
    loan_repayments = 0.0
    dividends_paid = 0.0
    
    cash_from_financing = loan_proceeds - loan_repayments - dividends_paid
    
    # Net change in cash
    net_cash_change = (
        cash_from_operations +
        cash_from_investing +
        cash_from_financing
    )
    
    # Get beginning and ending cash balances
    beginning_cash = _get_cash_balance(db, company_id, start_date, before=True)
    ending_cash = beginning_cash + net_cash_change
    
    return {
        "company_id": company_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "operating_activities": {
            "net_income": round(net_income, 2),
            "adjustments": {
                "depreciation_amortization": round(depreciation_amortization, 2),
                "working_capital_changes": round(working_capital_change, 2)
            },
            "total": round(cash_from_operations, 2)
        },
        "investing_activities": {
            "capital_expenditures": round(capital_expenditures, 2),
            "total": round(cash_from_investing, 2)
        },
        "financing_activities": {
            "loan_proceeds": round(loan_proceeds, 2),
            "loan_repayments": round(loan_repayments, 2),
            "dividends_paid": round(dividends_paid, 2),
            "total": round(cash_from_financing, 2)
        },
        "net_cash_change": round(net_cash_change, 2),
        "beginning_cash": round(beginning_cash, 2),
        "ending_cash": round(ending_cash, 2)
    }


def _get_cash_balance(
    db: Session,
    company_id: str,
    as_of_date: date,
    before: bool = False
) -> float:
    """
    Get cash balance as of a specific date.
    
    Args:
        db: Database session
        company_id: Company ID
        as_of_date: Date to calculate balance
        before: If True, get balance before this date
        
    Returns:
        Cash balance
    """
    if before:
        jes = db.query(JournalEntryDB).filter(
            and_(
                JournalEntryDB.company_id == company_id,
                JournalEntryDB.status == "posted",
                JournalEntryDB.date < as_of_date
            )
        ).all()
    else:
        jes = db.query(JournalEntryDB).filter(
            and_(
                JournalEntryDB.company_id == company_id,
                JournalEntryDB.status == "posted",
                JournalEntryDB.date <= as_of_date
            )
        ).all()
    
    cash_balance = 0.0
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            # Cash accounts typically start with 1000
            if 'Cash' in account or account.startswith('1000'):
                cash_balance += line['debit'] - line['credit']
    
    return cash_balance

