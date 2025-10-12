"""Automation performance metrics."""
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.db.models import JournalEntryDB, TransactionDB, ReconciliationDB


def get_automation_metrics(
    db: Session,
    company_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate automation performance metrics.
    
    Args:
        db: Database session
        company_id: Company ID filter
        days: Number of days to analyze
        
    Returns:
        Automation metrics
    """
    since_date = datetime.now().date() - timedelta(days=days)
    
    # Total journal entries created
    total_jes = db.query(func.count(JournalEntryDB.je_id)).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.created_at >= since_date
        )
    ).scalar() or 0
    
    # Auto-approved (not needing review)
    auto_approved = db.query(func.count(JournalEntryDB.je_id)).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.created_at >= since_date,
            JournalEntryDB.needs_review == 0
        )
    ).scalar() or 0
    
    # Needing review
    needs_review = db.query(func.count(JournalEntryDB.je_id)).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.created_at >= since_date,
            JournalEntryDB.needs_review == 1
        )
    ).scalar() or 0
    
    # Posted entries
    posted = db.query(func.count(JournalEntryDB.je_id)).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.created_at >= since_date,
            JournalEntryDB.status == "posted"
        )
    ).scalar() or 0
    
    # Reconciliation stats
    total_txns = db.query(func.count(TransactionDB.txn_id)).filter(
        and_(
            TransactionDB.company_id == company_id,
            TransactionDB.date >= since_date
        )
    ).scalar() or 0
    
    matched_txns = db.query(func.count(ReconciliationDB.id.distinct())).filter(
        ReconciliationDB.txn_id.in_(
            db.query(TransactionDB.txn_id).filter(
                and_(
                    TransactionDB.company_id == company_id,
                    TransactionDB.date >= since_date
                )
            )
        )
    ).scalar() or 0
    
    # Calculate percentages
    auto_approval_rate = (auto_approved / total_jes * 100) if total_jes > 0 else 0.0
    review_rate = (needs_review / total_jes * 100) if total_jes > 0 else 0.0
    recon_match_rate = (matched_txns / total_txns * 100) if total_txns > 0 else 0.0
    
    # Average confidence
    avg_confidence = db.query(func.avg(JournalEntryDB.confidence)).filter(
        and_(
            JournalEntryDB.company_id == company_id,
            JournalEntryDB.created_at >= since_date
        )
    ).scalar() or 0.0
    
    return {
        "company_id": company_id,
        "period_days": days,
        "since_date": since_date.isoformat(),
        "journal_entries": {
            "total": total_jes,
            "auto_approved": auto_approved,
            "needs_review": needs_review,
            "posted": posted
        },
        "rates": {
            "auto_approval_rate": round(auto_approval_rate, 2),
            "review_rate": round(review_rate, 2),
            "recon_match_rate": round(recon_match_rate, 2)
        },
        "transactions": {
            "total": total_txns,
            "matched": matched_txns,
            "unmatched": total_txns - matched_txns
        },
        "avg_confidence": round(avg_confidence, 2),
        "targets": {
            "auto_approval_target": 80.0,
            "recon_match_target": 90.0,
            "review_target_max": 20.0
        },
        "status": {
            "auto_approval_met": auto_approval_rate >= 80.0,
            "recon_match_met": recon_match_rate >= 90.0,
            "review_met": review_rate <= 20.0
        }
    }


def get_automation_trend(
    db: Session,
    company_id: str,
    days: int = 90
) -> List[Dict[str, Any]]:
    """
    Get automation rate trend over time (weekly buckets).
    
    Args:
        db: Database session
        company_id: Company ID
        days: Number of days to analyze
        
    Returns:
        List of weekly metrics
    """
    since_date = datetime.now().date() - timedelta(days=days)
    weeks = []
    
    # Generate weekly buckets
    current_date = since_date
    end_date = datetime.now().date()
    
    while current_date < end_date:
        week_end = min(current_date + timedelta(days=7), end_date)
        
        # Calculate metrics for this week
        week_metrics = get_automation_metrics(db, company_id, 7)
        week_metrics['week_start'] = current_date.isoformat()
        week_metrics['week_end'] = week_end.isoformat()
        
        weeks.append(week_metrics)
        current_date = week_end
    
    return weeks

