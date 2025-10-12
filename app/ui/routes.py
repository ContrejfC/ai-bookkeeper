"""
Wave-1 UI Routes (Sprint 9 Post-RC).

Implements:
- Reason-aware review page with filters
- Metrics dashboard
- Export Center polish
"""
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import json
import os

from app.ui.rbac import User, get_current_user, Role
from app.db.session import get_db
from app.db.models import BillingSubscriptionDB

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Review Page (Reason-Aware)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/review", response_class=HTMLResponse)
async def review_page(
    request: Request,
    tenant_id: Optional[str] = Query(None),
    reason_filter: Optional[str] = Query(None),
    vendor_filter: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None)
):
    """
    Review inbox with reason-aware filtering.
    
    Query params:
    - tenant_id: Filter by tenant
    - reason_filter: Filter by not_auto_post_reason
    - vendor_filter: Filter by vendor
    - min_amount, max_amount: Amount range
    """
    # Mock transactions for demo
    transactions = [
        {
            "txn_id": "txn-001",
            "date": "2024-10-11",
            "vendor": "Office Depot",
            "amount": 145.50,
            "proposed_account": "Office Supplies",
            "calibrated_p": 0.86,
            "auto_post_eligible": False,
            "not_auto_post_reason": "below_threshold",
            "threshold_used": 0.90,
            "cold_start": {"eligible": True, "label_count": 2}
        },
        {
            "txn_id": "txn-002",
            "date": "2024-10-11",
            "vendor": "NewVendor Inc",
            "amount": 2500.00,
            "proposed_account": "Professional Services",
            "calibrated_p": 0.95,
            "auto_post_eligible": False,
            "not_auto_post_reason": "cold_start",
            "threshold_used": 0.90,
            "cold_start": {"eligible": False, "label_count": 1}
        },
        {
            "txn_id": "txn-003",
            "date": "2024-10-10",
            "vendor": "Amazon.com",
            "amount": 89.99,
            "proposed_account": "Office Supplies",
            "calibrated_p": 0.93,
            "auto_post_eligible": False,
            "not_auto_post_reason": "imbalance",
            "threshold_used": 0.90,
            "cold_start": {"eligible": True, "label_count": 15}
        },
        {
            "txn_id": "txn-004",
            "date": "2024-10-10",
            "vendor": "Staples",
            "amount": 45.00,
            "proposed_account": "Office Supplies",
            "calibrated_p": 0.97,
            "auto_post_eligible": True,
            "not_auto_post_reason": None,
            "threshold_used": 0.90,
            "cold_start": {"eligible": True, "label_count": 20}
        }
    ]
    
    # Apply filters
    filtered_txns = transactions
    
    if reason_filter:
        filtered_txns = [t for t in filtered_txns if t.get("not_auto_post_reason") == reason_filter]
    
    if vendor_filter:
        filtered_txns = [t for t in filtered_txns if vendor_filter.lower() in t["vendor"].lower()]
    
    if min_amount is not None:
        filtered_txns = [t for t in filtered_txns if t["amount"] >= min_amount]
    
    if max_amount is not None:
        filtered_txns = [t for t in filtered_txns if t["amount"] <= max_amount]
    
    # Get reason counts for filter chips
    reason_counts = {
        "below_threshold": 87,
        "cold_start": 42,
        "imbalance": 2,
        "budget_fallback": 0,
        "anomaly": 8,
        "rule_conflict": 3
    }
    
    return templates.TemplateResponse("review.html", {
        "request": request,
        "transactions": filtered_txns,
        "reason_counts": reason_counts,
        "active_reason_filter": reason_filter,
        "vendor_filter": vendor_filter,
        "min_amount": min_amount,
        "max_amount": max_amount
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Metrics Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/metrics", response_class=HTMLResponse)
async def metrics_page(
    request: Request,
    tenant_id: Optional[str] = Query(None),
    period: str = Query("30d")
):
    """
    Metrics dashboard pulling from /api/metrics/latest.
    
    Query params:
    - tenant_id: Filter by tenant
    - period: Time window (7d, 30d, 90d)
    """
    # Mock metrics (in production, would call /api/metrics/latest)
    window_days = int(period.replace("d", ""))
    window_start = datetime.now() - timedelta(days=window_days)
    
    metrics = {
        "schema_version": "1.0",
        "period": period,
        "window_start_ts": window_start.isoformat(),
        "window_end_ts": datetime.now().isoformat(),
        "population_n": 1234,
        
        # Core metrics
        "automation_rate": 0.847,
        "auto_post_rate": 0.823,
        "review_rate": 0.177,
        "reconciliation_rate": 0.956,
        "je_imbalance_count": 2,
        
        # Model quality
        "brier_score": 0.118,
        "calibration_method": "isotonic",
        "ece_calibrated": 0.029,
        "ece_bins": [
            {"bin": "0.0-0.1", "pred": 0.052, "obs": 0.048, "count": 87},
            {"bin": "0.1-0.2", "pred": 0.151, "obs": 0.155, "count": 64},
            {"bin": "0.2-0.4", "pred": 0.298, "obs": 0.305, "count": 152},
            {"bin": "0.4-0.6", "pred": 0.512, "obs": 0.508, "count": 201},
            {"bin": "0.6-0.7", "pred": 0.653, "obs": 0.641, "count": 134},
            {"bin": "0.7-0.8", "pred": 0.748, "obs": 0.761, "count": 187},
            {"bin": "0.8-0.9", "pred": 0.851, "obs": 0.843, "count": 243},
            {"bin": "0.9-1.0", "pred": 0.947, "obs": 0.952, "count": 412}
        ],
        
        # Gating
        "gating_threshold": 0.90,
        "not_auto_post_counts": {
            "below_threshold": 87,
            "cold_start": 42,
            "imbalance": 2,
            "budget_fallback": 0,
            "anomaly": 8,
            "rule_conflict": 3
        },
        
        # Drift
        "psi_vendor": 0.043,
        "psi_amount": 0.021,
        "ks_vendor": 0.089,
        "ks_amount": 0.034,
        
        # Costs
        "llm_calls_per_txn": 0.042,
        "unit_cost_per_txn": 0.0023,
        "llm_budget_status": {
            "tenant_spend_usd": 12.45,
            "global_spend_usd": 847.32,
            "tenant_cap_usd": 50.00,
            "global_cap_usd": 1000.00,
            "fallback_active": False
        },
        
        # Versions
        "ruleset_version_id": "v0.4.13",
        "model_version_id": "m1.2.0"
    }
    
    # Validation: Check if reason counts reconcile
    total_not_auto_posted = sum(metrics["not_auto_post_counts"].values())
    expected_not_auto_posted = int(metrics["population_n"] * metrics["review_rate"])
    counts_reconcile = abs(total_not_auto_posted - expected_not_auto_posted) <= 5
    
    return templates.TemplateResponse("metrics.html", {
        "request": request,
        "metrics": metrics,
        "tenant_id": tenant_id,
        "period": period,
        "counts_reconcile": counts_reconcile,
        "total_not_auto_posted": total_not_auto_posted,
        "expected_not_auto_posted": expected_not_auto_posted
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Export Center
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/export", response_class=HTMLResponse)
async def export_page(request: Request):
    """
    Export Center with QBO CSV export and idempotency tracking.
    """
    # Mock export history
    export_history = [
        {
            "export_id": "exp-001",
            "timestamp": "2024-10-11T10:30:00Z",
            "posted_count": 5,
            "skipped_count": 0,
            "total_lines": 10,
            "status": "success"
        },
        {
            "export_id": "exp-002",
            "timestamp": "2024-10-11T11:00:00Z",
            "posted_count": 0,
            "skipped_count": 5,
            "total_lines": 0,
            "status": "success",
            "note": "Re-export (all duplicates)"
        }
    ]
    
    # Mock qbo_export_log entries
    qbo_log_entries = [
        {
            "external_id_short": "a3f7d8c2e1b4f5a6",  # First 16 hex (displaying first 32 in UI)
            "external_id_full": "a3f7d8c2e1b4f5a67890abcdef123456",
            "je_id": "je-001",
            "date": "2024-10-10",
            "status": "posted",
            "first_export_ts": "2024-10-11T10:30:00Z",
            "last_attempted_ts": "2024-10-11T10:30:00Z",
            "attempt_count": 1
        },
        {
            "external_id_short": "b2c3d4e5f6a78901",
            "external_id_full": "b2c3d4e5f6a789012345cdef67890abc",
            "je_id": "je-002",
            "date": "2024-10-10",
            "status": "posted",
            "first_export_ts": "2024-10-11T10:30:00Z",
            "last_attempted_ts": "2024-10-11T11:00:00Z",
            "attempt_count": 2
        }
    ]
    
    return templates.TemplateResponse("export.html", {
        "request": request,
        "export_history": export_history,
        "qbo_log_entries": qbo_log_entries
    })


@router.post("/export/qbo", response_class=HTMLResponse)
async def trigger_export(request: Request):
    """
    Trigger QBO CSV export (htmx endpoint).
    """
    # In production, would call actual export endpoint
    # For now, return success fragment
    result = {
        "new": 3,
        "skipped": 2,
        "total_lines": 6,
        "timestamp": datetime.now().isoformat()
    }
    
    return f"""
    <div class="bg-green-50 border border-green-200 rounded p-4 mb-4">
        <h3 class="font-semibold text-green-800">Export Complete</h3>
        <ul class="mt-2 text-sm text-green-700">
            <li>Posted: {result['new']} journal entries ({result['total_lines']} lines)</li>
            <li>Skipped: {result['skipped']} (duplicates)</li>
            <li>Timestamp: {result['timestamp']}</li>
        </ul>
    </div>
    """


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Wave-2 Phase 1: Firm Console, Rules Console, Audit Log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/firm", response_class=HTMLResponse)
async def firm_console(
    request: Request,
    user: User = Depends(get_current_user)
):
    """
    Firm Console - Multi-tenant management dashboard (Wave-2 Phase 1).
    
    RBAC:
    - Owner: sees all tenants, can modify settings
    - Staff: only sees assigned tenants, read-only
    """
    # Mock tenants data
    # Use database tenants instead of mock data
    from sqlalchemy.orm import Session
    from app.db.session import get_db
    from app.db.models import UserDB, UserTenantDB
    
    # Filter by RBAC
    all_tenant_ids = [t["id"] for t in MOCK_TENANTS]
    visible_tenant_ids = user.get_visible_tenants(all_tenant_ids)
    
    filtered_tenants = [
        t for t in MOCK_TENANTS
        if t["id"] in visible_tenant_ids
    ]
    
    return templates.TemplateResponse("firm.html", {
        "request": request,
        "tenants": filtered_tenants,
        "user_role": user.role.value,
        "can_modify": user.role == Role.OWNER
    })


@router.get("/rules", response_class=HTMLResponse)
async def rules_console(
    request: Request,
    active_tab: Optional[str] = Query("candidates")
):
    """
    Rules Console - Adaptive rule learning workflow (Wave-2 Phase 1).
    
    Tabs:
    - Candidates: Rules pending review
    - Accepted: Promoted rules (with rollback)
    - Rejected: Declined candidates
    """
    # Mock rule candidates
    candidates = [
        {
            "id": "cand-001",
            "vendor_pattern": "office depot*",
            "suggested_account": "Office Supplies",
            "evidence": {
                "count": 24,
                "precision": 0.96,
                "std_dev": 0.042
            }
        },
        {
            "id": "cand-002",
            "vendor_pattern": "amazon.com*",
            "suggested_account": "Office Supplies",
            "evidence": {
                "count": 47,
                "precision": 0.87,
                "std_dev": 0.128
            }
        }
    ]
    
    # Mock accepted rules
    accepted = [
        {
            "version_id": "v1.0.5",
            "vendor_pattern": "staples*",
            "account": "Office Supplies",
            "promoted_by": "admin@example.com",
            "timestamp": "2024-10-10T14:30:00Z"
        }
    ]
    
    # Mock rejected rules
    rejected = [
        {
            "vendor_pattern": "walmart*",
            "suggested_account": "Office Supplies",
            "rejected_by": "admin@example.com",
            "reason": "Too broad - needs more specific categorization",
            "timestamp": "2024-10-09T11:20:00Z"
        }
    ]
    
    return templates.TemplateResponse("rules.html", {
        "request": request,
        "active_tab": active_tab,
        "candidates": candidates,
        "accepted": accepted,
        "rejected": rejected
    })


@router.get("/audit", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1)
):
    """
    Audit Log Viewer - Complete decision history (Wave-2 Phase 1).
    
    Filterable by:
    - Date range
    - Tenant
    - Vendor
    - Action (auto_posted, reviewed, approved, rejected)
    - User
    
    Supports CSV export and deep-links to /explain/{txn_id}.
    """
    # Mock audit entries
    audit_entries = [
        {
            "timestamp": "2024-10-11T10:30:00Z",
            "tenant_id": "pilot-acme-corp-082aceed",
            "tenant_name": "Acme Corp",
            "txn_id": "txn-20241011-001",
            "vendor_normalized": "office depot",
            "action": "auto_posted",
            "not_auto_post_reason": None,
            "calibrated_p": 0.94,
            "threshold_used": 0.90,
            "user_id": "system",
            "user_email": None
        },
        {
            "timestamp": "2024-10-11T09:15:00Z",
            "tenant_id": "pilot-acme-corp-082aceed",
            "tenant_name": "Acme Corp",
            "txn_id": "txn-20241011-002",
            "vendor_normalized": "new vendor inc",
            "action": "reviewed",
            "not_auto_post_reason": "cold_start",
            "calibrated_p": 0.95,
            "threshold_used": 0.90,
            "user_id": "user-admin-001",
            "user_email": "admin@example.com"
        },
        {
            "timestamp": "2024-10-10T16:45:00Z",
            "tenant_id": "pilot-beta-accounting-inc-31707447",
            "tenant_name": "Beta Inc",
            "txn_id": "txn-20241010-055",
            "vendor_normalized": "amazon.com",
            "action": "approved",
            "not_auto_post_reason": "below_threshold",
            "calibrated_p": 0.86,
            "threshold_used": 0.92,
            "user_id": "user-staff-002",
            "user_email": "staff@betainc.com"
        }
    ]
    
    # Apply filters (mock filtering)
    filtered_entries = audit_entries
    if tenant_id:
        filtered_entries = [e for e in filtered_entries if e["tenant_id"] == tenant_id]
    if vendor:
        filtered_entries = [e for e in filtered_entries if vendor.lower() in e["vendor_normalized"].lower()]
    if action:
        filtered_entries = [e for e in filtered_entries if e["action"] == action]
    
    return templates.TemplateResponse("audit.html", {
        "request": request,
        "audit_entries": filtered_entries,
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
            "tenant_id": tenant_id,
            "vendor": vendor,
            "action": action
        },
        "page": page,
        "total_entries": len(filtered_entries)
    })

