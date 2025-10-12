"""CSV export functionality for journal entries and reconciliation results."""
import csv
from typing import List, TextIO
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import JournalEntryDB, TransactionDB, ReconciliationDB


def export_journal_entries_csv(db: Session, output_file: TextIO, status: str = None):
    """
    Export journal entries to CSV format.
    
    Args:
        db: Database session
        output_file: File-like object to write to
        status: Optional filter by status (proposed, approved, posted)
    """
    # Query journal entries
    query = db.query(JournalEntryDB)
    if status:
        query = query.filter(JournalEntryDB.status == status)
    
    jes = query.order_by(JournalEntryDB.date).all()
    
    # Write CSV header
    writer = csv.writer(output_file)
    writer.writerow([
        "JE ID",
        "Date",
        "Account",
        "Debit",
        "Credit",
        "Status",
        "Source Transaction",
        "Memo",
        "Confidence"
    ])
    
    # Write journal entry lines
    for je in jes:
        for line in je.lines:
            writer.writerow([
                je.je_id,
                je.date.strftime("%Y-%m-%d"),
                line['account'],
                f"{line['debit']:.2f}" if line['debit'] > 0 else "",
                f"{line['credit']:.2f}" if line['credit'] > 0 else "",
                je.status,
                je.source_txn_id or "",
                je.memo or "",
                f"{je.confidence:.2f}"
            ])


def export_reconciliation_csv(db: Session, output_file: TextIO):
    """
    Export reconciliation results to CSV format.
    
    Args:
        db: Database session
        output_file: File-like object to write to
    """
    # Query reconciliations
    recons = db.query(ReconciliationDB).order_by(ReconciliationDB.created_at).all()
    
    # Write CSV header
    writer = csv.writer(output_file)
    writer.writerow([
        "Transaction ID",
        "Journal Entry ID",
        "Match Type",
        "Match Score",
        "Transaction Date",
        "Transaction Amount",
        "Transaction Description",
        "Reconciled At"
    ])
    
    # Write reconciliation records
    for recon in recons:
        txn = db.query(TransactionDB).filter(TransactionDB.txn_id == recon.txn_id).first()
        
        writer.writerow([
            recon.txn_id,
            recon.je_id,
            recon.match_type,
            f"{recon.match_score:.2f}",
            txn.date.strftime("%Y-%m-%d") if txn else "",
            f"{txn.amount:.2f}" if txn else "",
            txn.description if txn else "",
            recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else ""
        ])


def export_general_ledger_csv(db: Session, output_file: TextIO, start_date: str = None, end_date: str = None):
    """
    Export general ledger (all posted journal entries) to CSV.
    
    Args:
        db: Database session
        output_file: File-like object to write to
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    """
    # Query posted journal entries
    query = db.query(JournalEntryDB).filter(JournalEntryDB.status == "posted")
    
    if start_date:
        query = query.filter(JournalEntryDB.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(JournalEntryDB.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    
    jes = query.order_by(JournalEntryDB.date, JournalEntryDB.je_id).all()
    
    # Write CSV header
    writer = csv.writer(output_file)
    writer.writerow([
        "Date",
        "JE ID",
        "Account",
        "Debit",
        "Credit",
        "Memo"
    ])
    
    # Write ledger entries
    for je in jes:
        for line in je.lines:
            writer.writerow([
                je.date.strftime("%Y-%m-%d"),
                je.je_id,
                line['account'],
                f"{line['debit']:.2f}",
                f"{line['credit']:.2f}",
                je.memo or ""
            ])


def export_trial_balance_csv(db: Session, output_file: TextIO, as_of_date: str = None):
    """
    Export trial balance (account balances) to CSV.
    
    Args:
        db: Database session
        output_file: File-like object to write to
        as_of_date: Optional date (YYYY-MM-DD) for balance calculation
    """
    # Query posted journal entries
    query = db.query(JournalEntryDB).filter(JournalEntryDB.status == "posted")
    
    if as_of_date:
        query = query.filter(JournalEntryDB.date <= datetime.strptime(as_of_date, "%Y-%m-%d").date())
    
    jes = query.all()
    
    # Calculate balances by account
    account_balances = {}
    
    for je in jes:
        for line in je.lines:
            account = line['account']
            if account not in account_balances:
                account_balances[account] = {'debit': 0.0, 'credit': 0.0}
            
            account_balances[account]['debit'] += line['debit']
            account_balances[account]['credit'] += line['credit']
    
    # Write CSV header
    writer = csv.writer(output_file)
    writer.writerow([
        "Account",
        "Total Debits",
        "Total Credits",
        "Balance (Debit - Credit)"
    ])
    
    # Write balances
    total_debits = 0.0
    total_credits = 0.0
    
    for account in sorted(account_balances.keys()):
        bal = account_balances[account]
        balance = bal['debit'] - bal['credit']
        
        writer.writerow([
            account,
            f"{bal['debit']:.2f}",
            f"{bal['credit']:.2f}",
            f"{balance:.2f}"
        ])
        
        total_debits += bal['debit']
        total_credits += bal['credit']
    
    # Write totals
    writer.writerow([])
    writer.writerow([
        "TOTALS",
        f"{total_debits:.2f}",
        f"{total_credits:.2f}",
        f"{total_debits - total_credits:.2f}"
    ])

