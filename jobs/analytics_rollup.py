"""
Daily Analytics Rollup Job (Phase 2b).

Aggregates event logs into daily reports.
"""
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
import sys


def run_rollup(date: str = None):
    """
    Create daily rollup report from event logs.
    
    Args:
        date: YYYYMMDD format (defaults to yesterday)
        
    Outputs:
        reports/analytics/daily_<YYYY-MM-DD>.json
    """
    if not date:
        yesterday = datetime.utcnow() - timedelta(days=1)
        date = yesterday.strftime("%Y%m%d")
    
    # Read events file
    events_file = f"logs/analytics/events_{date}.jsonl"
    
    if not os.path.exists(events_file):
        print(f"⚠️  No events file for {date}: {events_file}")
        return
    
    # Aggregate events
    totals = defaultdict(int)
    by_tenant = defaultdict(lambda: defaultdict(int))
    by_user_role = defaultdict(int)
    
    event_count = 0
    
    with open(events_file, "r") as f:
        for line in f:
            try:
                event = json.loads(line)
                event_type = event.get("event")
                tenant_id = event.get("tenant_id")
                user_role = event.get("user_role")
                
                if event_type:
                    totals[event_type] += 1
                    event_count += 1
                
                if tenant_id:
                    by_tenant[tenant_id][event_type] += 1
                
                if user_role:
                    by_user_role[user_role] += 1
            
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping invalid JSON line: {e}")
                continue
    
    # Format date for output (YYYY-MM-DD)
    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    
    # Create report
    report = {
        "date": formatted_date,
        "date_raw": date,
        "totals": dict(totals),
        "by_tenant": {k: dict(v) for k, v in by_tenant.items()},
        "by_user_role": dict(by_user_role),
        "summary": {
            "total_events": event_count,
            "unique_tenants": len(by_tenant),
            "unique_event_types": len(totals)
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Write report
    os.makedirs("reports/analytics", exist_ok=True)
    report_path = f"reports/analytics/daily_{formatted_date}.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Rollup complete: {report_path}")
    print(f"   Total events: {event_count}")
    print(f"   Unique tenants: {len(by_tenant)}")
    print(f"   Event types: {len(totals)}")
    
    return report_path


def run_rollup_last_n_days(n: int = 7):
    """
    Run rollup for last N days.
    
    Useful for backfilling or catching up.
    """
    for i in range(n):
        date_obj = datetime.utcnow() - timedelta(days=i+1)
        date_str = date_obj.strftime("%Y%m%d")
        
        try:
            run_rollup(date_str)
        except Exception as e:
            print(f"⚠️  Error rolling up {date_str}: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--last7":
            run_rollup_last_n_days(7)
        else:
            # Specific date
            run_rollup(sys.argv[1])
    else:
        # Yesterday
        run_rollup()

