"""
Product Analytics API (Phase 2b).

Endpoints for viewing analytics reports.
"""
import os
import json
import glob
from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime, timedelta


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/last7")
async def get_last_7_days() -> List[Dict[str, Any]]:
    """
    Get last 7 days of analytics reports.
    
    Returns list of daily reports sorted newest first.
    """
    reports = []
    
    # Look for last 7 days
    for i in range(7):
        date_obj = datetime.utcnow() - timedelta(days=i)
        formatted_date = date_obj.strftime("%Y-%m-%d")
        report_path = f"reports/analytics/daily_{formatted_date}.json"
        
        if os.path.exists(report_path):
            try:
                with open(report_path, "r") as f:
                    report = json.load(f)
                    reports.append(report)
            except:
                pass
    
    # If no reports found, return sample data
    if not reports:
        # Generate sample report for demonstration
        today = datetime.utcnow().strftime("%Y-%m-%d")
        reports = [{
            "date": today,
            "totals": {
                "page_view": 145,
                "review_action_approve": 34,
                "review_action_reject": 12,
                "export_run_posted": 5,
                "metrics_view": 23
            },
            "by_tenant": {
                "tenant-alpha": {
                    "page_view": 87,
                    "review_action_approve": 21
                },
                "tenant-beta": {
                    "page_view": 58,
                    "review_action_approve": 13
                }
            },
            "summary": {
                "total_events": 219,
                "unique_tenants": 2,
                "unique_event_types": 5
            },
            "note": "Sample data - no real events yet"
        }]
    
    return reports


@router.get("/events/types")
async def get_event_types() -> Dict[str, str]:
    """Get list of available event types."""
    from app.analytics.sink import (
        EVENT_PAGE_VIEW, EVENT_REVIEW_APPROVE, EVENT_REVIEW_REJECT,
        EVENT_BULK_APPROVE, EVENT_EXPLAIN_OPEN, EVENT_EXPORT_RUN_POSTED,
        EVENT_EXPORT_RUN_SKIPPED, EVENT_METRICS_VIEW,
        EVENT_BILLING_CHECKOUT_STARTED, EVENT_BILLING_CHECKOUT_COMPLETED,
        EVENT_NOTIFICATION_SENT
    )
    
    return {
        "page_view": EVENT_PAGE_VIEW,
        "review_approve": EVENT_REVIEW_APPROVE,
        "review_reject": EVENT_REVIEW_REJECT,
        "bulk_approve": EVENT_BULK_APPROVE,
        "explain_open": EVENT_EXPLAIN_OPEN,
        "export_posted": EVENT_EXPORT_RUN_POSTED,
        "export_skipped": EVENT_EXPORT_RUN_SKIPPED,
        "metrics_view": EVENT_METRICS_VIEW,
        "billing_checkout_started": EVENT_BILLING_CHECKOUT_STARTED,
        "billing_checkout_completed": EVENT_BILLING_CHECKOUT_COMPLETED,
        "notification_sent": EVENT_NOTIFICATION_SENT
    }

