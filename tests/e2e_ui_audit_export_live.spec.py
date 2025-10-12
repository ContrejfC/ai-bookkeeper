"""
E2E UI Tests for Audit Log Export (Live Streaming).

Tests CSV download with filters and basic validation.
"""
import pytest
from fastapi.testclient import TestClient
import csv
from io import StringIO

from app.api.main import app
from app.db.session import SessionLocal


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def auth_cookie(db):
    """Auth cookie."""
    response = client.post("/api/auth/login?use_cookie=true", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    return response.cookies


def test_e2e_audit_page_loads(db, auth_cookie):
    """Verify /audit page loads."""
    response = client.get("/audit", cookies=auth_cookie)
    
    assert response.status_code == 200
    content = response.content.decode()
    
    assert "audit" in content.lower()
    assert "export" in content.lower() or "download" in content.lower()
    
    print("✅ /audit page loads")


def test_e2e_export_csv_downloads(db, auth_cookie):
    """Verify CSV export button triggers download."""
    response = client.get("/api/audit/export.csv", cookies=auth_cookie)
    
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    
    # Parse CSV
    content = b"".join(response.iter_content()).decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    
    assert len(rows) > 0, "CSV should have at least header"
    
    # Check header
    expected_cols = [
        "timestamp", "tenant_id", "user_id", "action", "txn_id",
        "vendor_normalized", "calibrated_p", "threshold_used",
        "not_auto_post_reason", "cold_start_label_count",
        "ruleset_version_id", "model_version_id"
    ]
    
    assert rows[0] == expected_cols
    
    print(f"✅ CSV export downloads successfully ({len(rows)} rows)")


def test_e2e_export_with_filters(db, auth_cookie):
    """Verify export filters work."""
    # Export with tenant filter
    response_filtered = client.get(
        "/api/audit/export.csv?tenant_id=pilot-acme-corp-082aceed",
        cookies=auth_cookie
    )
    
    assert response_filtered.status_code == 200
    
    content = b"".join(response_filtered.iter_content()).decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    # Check that all rows have matching tenant_id (or empty for header actions)
    for i, row in enumerate(reader):
        if i >= 10:  # Check first 10 rows
            break
        if row["tenant_id"]:  # Skip empty tenant_id
            assert row["tenant_id"] == "pilot-acme-corp-082aceed"
    
    print("✅ Export filters work")


def test_e2e_export_csv_validation(db, auth_cookie):
    """Verify CSV structure is valid."""
    response = client.get("/api/audit/export.csv", cookies=auth_cookie)
    
    content = b"".join(response.iter_content()).decode('utf-8')
    reader = csv.reader(StringIO(content))
    
    rows = list(reader)
    expected_col_count = 12
    
    # Check all rows have correct column count
    for i, row in enumerate(rows):
        assert len(row) == expected_col_count, f"Row {i} has {len(row)} columns, expected {expected_col_count}"
    
    print(f"✅ CSV structure validated ({len(rows)} rows)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

