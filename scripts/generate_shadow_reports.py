#!/usr/bin/env python3
"""
Generate Shadow Reports for Pilot Tenants

Creates 7-day shadow reports showing automation candidates.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import DecisionAuditLogDB, TenantSettingsDB


def generate_shadow_report(db, tenant_id, days=7):
    """Generate shadow report for a tenant."""
    
    print(f"\nGenerating shadow report for {tenant_id}...")
    
    # Get tenant settings
    settings = db.query(TenantSettingsDB).filter_by(tenant_id=tenant_id).first()
    if not settings:
        print(f"⚠️  Tenant {tenant_id} not found")
        return None
    
    # Get decisions from last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    
    decisions = db.query(DecisionAuditLogDB).filter(
        DecisionAuditLogDB.tenant_id == tenant_id,
        DecisionAuditLogDB.timestamp >= start_date
    ).all()
    
    print(f"  Found {len(decisions)} decisions")
    
    # Analyze decisions
    total_transactions = len([d for d in decisions if d.txn_id])
    
    # Count by reason
    reason_counts = defaultdict(int)
    automation_candidates = []
    review_queue = []
    
    for decision in decisions:
        if not decision.txn_id:
            continue
        
        metadata = decision.metadata or {}
        reason = metadata.get("not_auto_post_reason")
        calibrated_p = metadata.get("calibrated_p", 0)
        threshold = metadata.get("threshold_used", settings.autopost_threshold)
        
        if reason:
            reason_counts[reason] += 1
            review_queue.append({
                "txn_id": decision.txn_id,
                "reason": reason,
                "calibrated_p": calibrated_p,
                "threshold": threshold,
                "timestamp": decision.timestamp.isoformat()
            })
        else:
            # Would have been auto-posted
            if calibrated_p >= threshold:
                automation_candidates.append({
                    "txn_id": decision.txn_id,
                    "calibrated_p": calibrated_p,
                    "timestamp": decision.timestamp.isoformat()
                })
    
    # Calculate metrics
    automation_rate = len(automation_candidates) / total_transactions if total_transactions > 0 else 0
    review_rate = len(review_queue) / total_transactions if total_transactions > 0 else 0
    
    # Build report
    report = {
        "tenant_id": tenant_id,
        "period": {
            "start": start_date.isoformat(),
            "end": datetime.utcnow().isoformat(),
            "days": days
        },
        "summary": {
            "total_transactions": total_transactions,
            "automation_candidates": len(automation_candidates),
            "review_queue": len(review_queue),
            "automation_rate": round(automation_rate, 3),
            "review_rate": round(review_rate, 3)
        },
        "settings": {
            "autopost_enabled": settings.autopost_enabled,
            "autopost_threshold": settings.autopost_threshold,
            "llm_budget": settings.llm_tenant_cap_usd
        },
        "reason_breakdown": dict(reason_counts),
        "top_automation_candidates": automation_candidates[:10],
        "top_review_items": review_queue[:10],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Save report
    os.makedirs("reports/shadow", exist_ok=True)
    report_path = f"reports/shadow/{tenant_id}_shadow_{days}d.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Report saved: {report_path}")
    print(f"  Automation rate: {automation_rate:.1%}")
    print(f"  Review queue: {len(review_queue)} items")
    
    return report


def main():
    """Generate shadow reports for all pilot tenants."""
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Shadow Report Generation")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    db = SessionLocal()
    
    try:
        # Get all pilot tenants
        pilot_tenants = db.query(TenantSettingsDB).filter(
            TenantSettingsDB.tenant_id.like("pilot-%")
        ).all()
        
        if not pilot_tenants:
            print("\n⚠️  No pilot tenants found.")
            print("Run: python3 scripts/create_pilot_tenants.py")
            return
        
        print(f"\nFound {len(pilot_tenants)} pilot tenants")
        
        reports = []
        for tenant in pilot_tenants:
            report = generate_shadow_report(db, tenant.tenant_id, days=7)
            if report:
                reports.append(report)
        
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Generated {len(reports)} shadow reports")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("Reports saved to: reports/shadow/")
        print()
        
        # Summary table
        print("Summary:")
        print(f"{'Tenant':<20} {'Transactions':<15} {'Auto Rate':<12} {'Review Queue':<15}")
        print("-" * 65)
        for report in reports:
            tenant_id = report["tenant_id"]
            total = report["summary"]["total_transactions"]
            auto_rate = report["summary"]["automation_rate"]
            review = report["summary"]["review_queue"]
            print(f"{tenant_id:<20} {total:<15} {auto_rate:<12.1%} {review:<15}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

