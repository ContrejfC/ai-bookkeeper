#!/usr/bin/env python3
"""
Weekly Access Snapshot Job (SOC 2 Min Controls).

Generates compliance evidence snapshot including:
- App users (id, email hash, role, tenants)
- Current env config flags (autopost_enabled, gating_threshold) per tenant
- GitHub org members (if GITHUB_ORG & GITHUB_TOKEN set)
- Render team members (if RENDER_API_KEY set)

Outputs:
- reports/compliance/access_snapshot_YYYYMMDD.csv
- reports/compliance/access_snapshot_YYYYMMDD.json

Run: python jobs/dump_access_snapshot.py
Schedule: Weekly (Sunday 02:00 UTC) via GitHub Actions
"""
import os
import sys
import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_session
from app.db.models import UserDB, UserTenantDB, TenantSettingsDB
from app.ops.logging import get_logger

logger = get_logger(__name__)

# Output directory
OUTPUT_DIR = Path("reports/compliance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Environment flags
GITHUB_ORG = os.getenv("GITHUB_ORG", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "").strip()


def hash_email(email: str) -> str:
    """Hash email for privacy (SHA-256, first 16 hex chars)."""
    return hashlib.sha256(email.encode()).hexdigest()[:16]


def get_app_users() -> List[Dict[str, Any]]:
    """
    Get app users with tenant assignments.
    
    Returns list of dicts with: user_id, email_hash, role, tenant_ids, is_active, created_at
    """
    session = next(get_db_session())
    
    try:
        users = session.query(UserDB).all()
        
        result = []
        for user in users:
            # Get tenant assignments
            tenant_links = session.query(UserTenantDB).filter_by(user_id=user.user_id).all()
            tenant_ids = [link.tenant_id for link in tenant_links]
            
            result.append({
                "user_id": user.user_id,
                "email_hash": hash_email(user.email),
                "role": user.role,
                "tenant_ids": tenant_ids,
                "tenant_count": len(tenant_ids),
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            })
        
        logger.info(f"Retrieved {len(result)} app users")
        return result
    
    finally:
        session.close()


def get_tenant_settings() -> List[Dict[str, Any]]:
    """
    Get tenant configuration flags.
    
    Returns list of dicts with: tenant_id, autopost_enabled, autopost_threshold, llm_cap
    """
    session = next(get_db_session())
    
    try:
        settings = session.query(TenantSettingsDB).all()
        
        result = []
        for s in settings:
            result.append({
                "tenant_id": s.tenant_id,
                "autopost_enabled": s.autopost_enabled,
                "autopost_threshold": s.autopost_threshold,
                "llm_tenant_cap_usd": s.llm_tenant_cap_usd,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "updated_by": s.updated_by,
            })
        
        logger.info(f"Retrieved {len(result)} tenant settings")
        return result
    
    finally:
        session.close()


def get_github_org_members() -> Optional[List[Dict[str, Any]]]:
    """
    Get GitHub org members (if credentials available).
    
    Returns list of dicts with: login, role, two_factor_enabled
    Or None if credentials not available.
    """
    if not GITHUB_ORG or not GITHUB_TOKEN:
        logger.info("GitHub credentials not set, skipping org member check")
        return None
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get org members
        url = f"https://api.github.com/orgs/{GITHUB_ORG}/members"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"GitHub API error: {response.status_code}")
            return None
        
        members = response.json()
        
        result = []
        for member in members:
            # Get member details (includes 2FA status if admin)
            member_url = f"https://api.github.com/users/{member['login']}"
            member_response = requests.get(member_url, headers=headers, timeout=10)
            
            if member_response.status_code == 200:
                member_data = member_response.json()
                result.append({
                    "login": member_data.get("login"),
                    "name": member_data.get("name"),
                    "role": member.get("role", "member"),
                    "site_admin": member.get("site_admin", False),
                })
        
        logger.info(f"Retrieved {len(result)} GitHub org members")
        return result
    
    except Exception as e:
        logger.error(f"Failed to fetch GitHub org members: {e}")
        return None


def get_render_team_members() -> Optional[List[Dict[str, Any]]]:
    """
    Get Render team members (if API key available).
    
    Returns list of dicts with: email_hash, role
    Or None if credentials not available.
    """
    if not RENDER_API_KEY:
        logger.info("Render API key not set, skipping team member check")
        return None
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
        
        # Note: Render API doesn't expose team members directly
        # This is a placeholder for when/if Render adds this endpoint
        # For now, return a note that manual verification is needed
        
        logger.info("Render team member API not available (manual verification required)")
        return [{
            "note": "Manual verification required",
            "docs": "https://render.com/docs/teams"
        }]
    
    except Exception as e:
        logger.error(f"Failed to fetch Render team members: {e}")
        return None


def generate_snapshot() -> Dict[str, Any]:
    """
    Generate complete access snapshot.
    
    Returns dict with all access data.
    """
    logger.info("Generating access snapshot...")
    
    snapshot = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "app_users": get_app_users(),
        "tenant_settings": get_tenant_settings(),
        "github_org_members": get_github_org_members(),
        "render_team_members": get_render_team_members(),
    }
    
    # Summary counts
    snapshot["summary"] = {
        "total_app_users": len(snapshot["app_users"]),
        "active_app_users": sum(1 for u in snapshot["app_users"] if u.get("is_active")),
        "total_tenants": len(snapshot["tenant_settings"]),
        "tenants_with_autopost": sum(1 for t in snapshot["tenant_settings"] if t.get("autopost_enabled")),
        "github_members": len(snapshot["github_org_members"]) if snapshot["github_org_members"] else "N/A",
        "render_members": "Manual verification required",
    }
    
    logger.info(f"Snapshot generated: {snapshot['summary']}")
    return snapshot


def save_snapshot_json(snapshot: Dict[str, Any], date_str: str) -> Path:
    """Save snapshot as JSON."""
    output_file = OUTPUT_DIR / f"access_snapshot_{date_str}.json"
    
    with open(output_file, "w") as f:
        json.dump(snapshot, f, indent=2)
    
    logger.info(f"Saved JSON snapshot: {output_file}")
    return output_file


def save_snapshot_csv(snapshot: Dict[str, Any], date_str: str) -> Path:
    """Save snapshot as CSV (flattened view)."""
    output_file = OUTPUT_DIR / f"access_snapshot_{date_str}.csv"
    
    # Flatten data for CSV
    rows = []
    
    # App users section
    for user in snapshot["app_users"]:
        rows.append({
            "section": "app_user",
            "identifier": user["user_id"],
            "email_hash": user["email_hash"],
            "role": user["role"],
            "tenant_count": user["tenant_count"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "last_login_at": user.get("last_login_at", ""),
        })
    
    # Tenant settings section
    for tenant in snapshot["tenant_settings"]:
        rows.append({
            "section": "tenant_setting",
            "identifier": tenant["tenant_id"],
            "email_hash": "",
            "role": "",
            "tenant_count": "",
            "is_active": "",
            "created_at": "",
            "last_login_at": "",
            "autopost_enabled": tenant["autopost_enabled"],
            "autopost_threshold": tenant["autopost_threshold"],
            "llm_cap_usd": tenant["llm_tenant_cap_usd"],
            "updated_at": tenant["updated_at"],
        })
    
    # GitHub members section
    if snapshot["github_org_members"]:
        for member in snapshot["github_org_members"]:
            rows.append({
                "section": "github_member",
                "identifier": member.get("login", ""),
                "email_hash": "",
                "role": member.get("role", ""),
                "tenant_count": "",
                "is_active": "",
                "created_at": "",
                "last_login_at": "",
                "site_admin": member.get("site_admin", False),
            })
    
    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Saved CSV snapshot: {output_file}")
    return output_file


def main():
    """Main entry point."""
    logger.info("=== Access Snapshot Job Started ===")
    
    try:
        # Generate snapshot
        snapshot = generate_snapshot()
        
        # Save outputs
        date_str = datetime.utcnow().strftime("%Y%m%d")
        json_file = save_snapshot_json(snapshot, date_str)
        csv_file = save_snapshot_csv(snapshot, date_str)
        
        # Update evidence index
        update_evidence_index(json_file, csv_file)
        
        logger.info("=== Access Snapshot Job Completed Successfully ===")
        print(f"✓ Snapshot saved: {json_file}")
        print(f"✓ Snapshot saved: {csv_file}")
        print(f"✓ Summary: {snapshot['summary']}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Access snapshot job failed: {e}", exc_info=True)
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def update_evidence_index(json_file: Path, csv_file: Path):
    """Update evidence index with new snapshot files."""
    index_file = Path("artifacts/compliance/EVIDENCE_INDEX.md")
    index_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare new entry
    entry = f"""
### Access Snapshot - {datetime.utcnow().strftime("%Y-%m-%d")}
- **JSON**: `{json_file.relative_to(Path.cwd())}`
- **CSV**: `{csv_file.relative_to(Path.cwd())}`
- **Generated**: {datetime.utcnow().isoformat()}Z
"""
    
    # Prepend to existing index
    if index_file.exists():
        existing_content = index_file.read_text()
        new_content = f"# Compliance Evidence Index\n\n{entry}\n{existing_content.split('\n', 2)[-1]}"
    else:
        new_content = f"# Compliance Evidence Index\n\n{entry}\n"
    
    index_file.write_text(new_content)
    logger.info(f"Updated evidence index: {index_file}")


if __name__ == "__main__":
    sys.exit(main())

