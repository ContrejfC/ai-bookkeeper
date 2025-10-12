"""Balance Sheet generation."""
from datetime import date
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models import JournalEntryDB


def generate_balance_sheet(
    db: Session,
    company_id: str,
    as_of_date: date
) -> Dict[str, Any]:
    """
    Generate Balance Sheet as of a specific date.
    
    Assets = Liabilities + Equity
    
    Args:
        db: Database session
        company_id: Company ID filter
        as_of_date: Date for balance sheet
        
    Returns:
        Balance sheet data structure
    """
    # Get all posted journal entries up to the date
    jes = db.query(JournalEntryDB).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.status == "posted",
            JournalEntryDB.date <= as_of_date
        )
    ).all()
    
    # Calculate account balances
    assets = {}
    liabilities = {}
    equity = {}
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            account_num = account.split()[0] if ' ' in account else account
            
            # Assets (1xxx) - debits increase
            if account_num.startswith('1'):
                if account not in assets:
                    assets[account] = 0.0
                assets[account] += line['debit'] - line['credit']
            
            # Liabilities (2xxx) - credits increase
            elif account_num.startswith('2'):
                if account not in liabilities:
                    liabilities[account] = 0.0
                liabilities[account] += line['credit'] - line['debit']
            
            # Equity (3xxx) - credits increase
            elif account_num.startswith('3'):
                if account not in equity:
                    equity[account] = 0.0
                equity[account] += line['credit'] - line['debit']
    
    # Calculate retained earnings (net income from revenue & expenses)
    # This would normally be calculated from prior periods, but for now
    # we'll calculate it from the current period P&L
    revenue = 0.0
    expenses = 0.0
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            account_num = account.split()[0] if ' ' in account else account
            
            # Revenue (8xxx)
            if account_num.startswith('8'):
                revenue += line['credit'] - line['debit']
            
            # Expenses (5xxx, 6xxx, 7xxx)
            elif account_num.startswith(('5', '6', '7')):
                expenses += line['debit'] - line['credit']
    
    net_income = revenue - expenses
    
    # Add retained earnings to equity
    if "3000 Retained Earnings" not in equity:
        equity["3000 Retained Earnings"] = 0.0
    equity["3000 Retained Earnings"] += net_income
    
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    total_equity = sum(equity.values())
    
    # Check balance (Assets = Liabilities + Equity)
    balance_check = abs(total_assets - (total_liabilities + total_equity))
    
    return {
        "company_id": company_id,
        "as_of_date": as_of_date.isoformat(),
        "assets": {
            "accounts": assets,
            "total": round(total_assets, 2)
        },
        "liabilities": {
            "accounts": liabilities,
            "total": round(total_liabilities, 2)
        },
        "equity": {
            "accounts": equity,
            "total": round(total_equity, 2)
        },
        "total_liabilities_and_equity": round(total_liabilities + total_equity, 2),
        "balanced": balance_check < 0.01,
        "balance_difference": round(balance_check, 2)
    }

