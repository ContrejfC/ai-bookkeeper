"""Profit & Loss statement generation."""
from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models import JournalEntryDB


def generate_pnl(
    db: Session,
    company_id: str,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Generate Profit & Loss statement for a date range.
    
    Args:
        db: Database session
        company_id: Company ID filter
        start_date: Start date
        end_date: End date
        
    Returns:
        P&L data structure
    """
    # Get posted journal entries
    jes = db.query(JournalEntryDB).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.status == "posted",
            JournalEntryDB.date >= start_date,
            JournalEntryDB.date <= end_date
        )
    ).all()
    
    # Calculate account balances
    revenue = {}
    expenses = {}
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            account_num = account.split()[0] if ' ' in account else account
            
            # Revenue accounts (8xxx) - credits increase revenue
            if account_num.startswith('8'):
                if account not in revenue:
                    revenue[account] = 0.0
                revenue[account] += line['credit'] - line['debit']
            
            # Expense accounts (5xxx, 6xxx, 7xxx) - debits increase expenses
            elif account_num.startswith(('5', '6', '7')):
                if account not in expenses:
                    expenses[account] = 0.0
                expenses[account] += line['debit'] - line['credit']
    
    total_revenue = sum(revenue.values())
    total_expenses = sum(expenses.values())
    net_income = total_revenue - total_expenses
    
    return {
        "company_id": company_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "revenue": {
            "accounts": revenue,
            "total": round(total_revenue, 2)
        },
        "expenses": {
            "accounts": expenses,
            "total": round(total_expenses, 2)
        },
        "net_income": round(net_income, 2),
        "margin_percent": round((net_income / total_revenue * 100) if total_revenue > 0 else 0.0, 2)
    }

