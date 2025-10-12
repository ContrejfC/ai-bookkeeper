"""
UI Screenshot Capture for Assessment (CEO Review)

Captures all UI states across routes for manual review.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# This would use Playwright or similar for automated capture
# For now, provides a comprehensive manual guide


def generate_screenshot_manifest():
    """Generate manifest of required screenshots."""
    
    manifest = {
        "assessment_date": datetime.utcnow().isoformat(),
        "ui_assessment_mode": True,
        "screenshots": [
            # Review page
            {
                "route": "/review",
                "states": [
                    {"file": "artifacts/ui-assessment/review_default.png", "desc": "Default view with 20+ transactions"},
                    {"file": "artifacts/ui-assessment/review_below_threshold.png", "desc": "Filter: below_threshold"},
                    {"file": "artifacts/ui-assessment/review_cold_start.png", "desc": "Filter: cold_start"},
                    {"file": "artifacts/ui-assessment/review_explain_open.png", "desc": "Explain drawer open"},
                    {"file": "artifacts/ui-assessment/review_bulk_approve.png", "desc": "Bulk approve prompt visible"},
                ]
            },
            # Receipts
            {
                "route": "/receipts",
                "states": [
                    {"file": "artifacts/ui-assessment/receipts_overlays.png", "desc": "OCR overlays visible"},
                    {"file": "artifacts/ui-assessment/receipts_tooltip.png", "desc": "Tooltip showing field + confidence"},
                    {"file": "artifacts/ui-assessment/receipts_messy.png", "desc": "Messy scan with lower confidence"},
                ]
            },
            # Metrics
            {
                "route": "/metrics",
                "states": [
                    {"file": "artifacts/ui-assessment/metrics_dashboard.png", "desc": "Reliability bins visible"},
                    {"file": "artifacts/ui-assessment/metrics_llm_cost.png", "desc": "LLM cost panel"},
                    {"file": "artifacts/ui-assessment/metrics_drift.png", "desc": "Drift charts (if available)"},
                ]
            },
            # Firm Console
            {
                "route": "/firm",
                "states": [
                    {"file": "artifacts/ui-assessment/firm_owner.png", "desc": "Owner view with settings modal"},
                    {"file": "artifacts/ui-assessment/firm_staff.png", "desc": "Staff view (limited access)"},
                    {"file": "artifacts/ui-assessment/firm_threshold_slider.png", "desc": "Threshold slider (AUTOPOST OFF)"},
                ]
            },
            # Rules
            {
                "route": "/rules",
                "states": [
                    {"file": "artifacts/ui-assessment/rules_candidates.png", "desc": "Candidates tab"},
                    {"file": "artifacts/ui-assessment/rules_dry_run.png", "desc": "Dry-run modal with projected impact"},
                ]
            },
            # Audit
            {
                "route": "/audit",
                "states": [
                    {"file": "artifacts/ui-assessment/audit_filtered.png", "desc": "Filtered view"},
                    {"file": "artifacts/ui-assessment/audit_export_confirm.png", "desc": "CSV export confirmation"},
                ]
            },
            # Export
            {
                "route": "/export",
                "states": [
                    {"file": "artifacts/ui-assessment/export_qbo.png", "desc": "QBO section"},
                    {"file": "artifacts/ui-assessment/export_xero.png", "desc": "Xero section (idempotent state)"},
                ]
            },
            # Billing
            {
                "route": "/billing",
                "states": [
                    {"file": "artifacts/ui-assessment/billing_not_configured.png", "desc": "Not configured banner"},
                    {"file": "artifacts/ui-assessment/billing_test_mode.png", "desc": "Test mode banner"},
                    {"file": "artifacts/ui-assessment/billing_active.png", "desc": "Active subscription"},
                ]
            },
            # Notifications
            {
                "route": "/settings/notifications",
                "states": [
                    {"file": "artifacts/ui-assessment/notif_dry_run.png", "desc": "Dry-run state"},
                    {"file": "artifacts/ui-assessment/notif_configured.png", "desc": "Configured with test send"},
                ]
            },
            # Onboarding
            {
                "route": "/onboarding",
                "states": [
                    {"file": "artifacts/ui-assessment/onboard_step1.png", "desc": "Step 1: CoA selection"},
                    {"file": "artifacts/ui-assessment/onboard_step2.png", "desc": "Step 2: Data ingest"},
                    {"file": "artifacts/ui-assessment/onboard_step3.png", "desc": "Step 3: Settings"},
                    {"file": "artifacts/ui-assessment/onboard_step4.png", "desc": "Step 4: Finish"},
                ]
            },
            # Analytics
            {
                "route": "/analytics",
                "states": [
                    {"file": "artifacts/ui-assessment/analytics_dashboard.png", "desc": "Last 7 days dashboard"},
                ]
            },
        ]
    }
    
    # Save manifest
    os.makedirs("artifacts/ui-assessment", exist_ok=True)
    with open("artifacts/ui-assessment/screenshot_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    print("=" * 80)
    print("UI SCREENSHOT MANIFEST GENERATED")
    print("=" * 80)
    print(f"\n📄 Manifest: artifacts/ui-assessment/screenshot_manifest.json")
    print(f"\n📸 Total screenshots required: {sum(len(s['states']) for s in manifest['screenshots'])}")
    
    print("\n" + "=" * 80)
    print("MANUAL CAPTURE INSTRUCTIONS")
    print("=" * 80)
    print("""
1. Start server in UI Assessment mode:
   $ export UI_ASSESSMENT=1
   $ uvicorn app.api.main:app --port 8000

2. Login as owner:
   Email: owner@pilot-smb-001.demo
   Password: demo-password-123

3. Navigate and capture each route/state:
   - Use browser screenshot (Cmd+Shift+4 on macOS)
   - Save to exact paths listed in manifest
   - Ensure UI_ASSESSMENT banner visible in each

4. For RBAC states, login as staff:
   Email: staff@pilot-smb-001.demo
   Password: demo-password-123

5. Verify all files exist:
   $ ls -la artifacts/ui-assessment/*.png
""")
    
    # Print checklist
    print("\n" + "=" * 80)
    print("SCREENSHOT CHECKLIST")
    print("=" * 80)
    for section in manifest["screenshots"]:
        print(f"\n{section['route']}:")
        for state in section["states"]:
            filename = Path(state['file']).name
            print(f"  [ ] {filename} — {state['desc']}")
    
    return manifest


if __name__ == "__main__":
    manifest = generate_screenshot_manifest()
    
    print("\n✅ Manifest generated. Follow instructions above to capture screenshots.")
    print("\n💡 TIP: Use Playwright for automation in production:")
    print("   pip install playwright")
    print("   playwright install chromium")

