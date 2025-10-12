"""
Tests for Audit CSV Export Streaming (Wave-2 Phase 1).

Tests:
- test_streams_large_export (100k rows)
- test_filters_restrict_rows
- test_csv_headers_and_columns
- test_timestamps_are_utc_iso8601
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import csv
from io import StringIO
from datetime import datetime, timedelta

from app.api.main import app
from app.db.session import SessionLocal
from app.db.models import DecisionAuditLogDB


client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Database session for tests."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def auth_token(db):
    """Get auth token for tests."""
    response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "magic_token": "dev"
    })
    return response.json()["token"]


@pytest.fixture(scope="module")
def seed_audit_100k(db):
    """Seed 100k audit entries for load testing."""
    import random
    
    print("Seeding 100k audit entries...")
    
    batch_size = 5000
    tenants = ["pilot-acme-corp-082aceed", "pilot-beta-accounting-inc-31707447"]
    vendors = ["office depot", "amazon.com", "staples", "walmart", "target"]
    actions = ["auto_posted", "reviewed", "approved"]
    reasons = ["below_threshold", "cold_start", "imbalance"]
    
    for i in range(0, 100000, batch_size):
        entries = []
        for j in range(batch_size):
            idx = i + j
            entry = DecisionAuditLogDB(
                timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
                tenant_id=random.choice(tenants),
                txn_id=f"txn-{idx}",
                vendor_normalized=random.choice(vendors),
                action=random.choice(actions),
                not_auto_post_reason=random.choice(reasons) if random.random() < 0.3 else None,
                calibrated_p=random.uniform(0.7, 0.99),
                threshold_used=0.90,
                user_id=random.choice(["system", "user-admin-001", "user-staff-001"]),
                cold_start_label_count=random.randint(0, 5) if random.random() < 0.2 else None
            )
            entries.append(entry)
        
        db.bulk_save_objects(entries)
        db.commit()
        
        if (i + batch_size) % 20000 == 0:
            print(f"  {i + batch_size} / 100000 seeded")
    
    print("✅ 100k audit entries seeded")
    yield
    
    # Cleanup (optional - can keep for multiple test runs)


def test_streams_large_export(db, auth_token, seed_audit_100k):
    """
    Verify CSV export streams 100k+ rows without OOM.
    
    Checks:
    - Response streams successfully
    - Row count ≥ 100,000
    - Memory usage stays bounded (monitored separately)
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Stream export
    response = client.get(
        "/api/audit/export.csv",
        headers={"Authorization": f"Bearer {auth_token}"},
        stream=True
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    # Count rows by streaming
    row_count = 0
    for line in response.iter_lines():
        row_count += 1
        if row_count % 10000 == 0:
            print(f"  Streamed {row_count} rows...")
    
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_delta = mem_after - mem_before
    
    print(f"✅ Streamed {row_count} rows successfully")
    print(f"   Memory delta: {mem_delta:.2f} MB")
    
    assert row_count >= 100001, f"Expected ≥100,001 rows (header + 100k data), got {row_count}"
    assert mem_delta < 150, f"Memory delta {mem_delta:.2f} MB exceeds 150MB limit"


def test_filters_restrict_rows(db, auth_token, seed_audit_100k):
    """
    Verify filters reduce row count correctly.
    
    Checks:
    - Unfiltered export has more rows
    - Tenant filter reduces rows
    - Action filter reduces rows
    - Multiple filters compound
    """
    # Unfiltered
    response_all = client.get(
        "/api/audit/export.csv",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    rows_all = sum(1 for _ in response_all.iter_lines())
    
    # Tenant filter
    response_tenant = client.get(
        "/api/audit/export.csv?tenant_id=pilot-acme-corp-082aceed",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    rows_tenant = sum(1 for _ in response_tenant.iter_lines())
    
    # Action filter
    response_action = client.get(
        "/api/audit/export.csv?action=auto_posted",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    rows_action = sum(1 for _ in response_action.iter_lines())
    
    # Combined filters
    response_combined = client.get(
        "/api/audit/export.csv?tenant_id=pilot-acme-corp-082aceed&action=auto_posted",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    rows_combined = sum(1 for _ in response_combined.iter_lines())
    
    print(f"Row counts:")
    print(f"  All: {rows_all}")
    print(f"  Tenant filter: {rows_tenant}")
    print(f"  Action filter: {rows_action}")
    print(f"  Combined: {rows_combined}")
    
    assert rows_tenant < rows_all, "Tenant filter should reduce rows"
    assert rows_action < rows_all, "Action filter should reduce rows"
    assert rows_combined < rows_tenant, "Combined filters should reduce further"
    assert rows_combined < rows_action, "Combined filters should reduce further"
    
    print(f"✅ Filters working correctly")


def test_csv_headers_and_columns(db, auth_token, seed_audit_100k):
    """
    Verify CSV structure is correct.
    
    Checks:
    - Header row matches specification
    - All rows have correct number of columns
    - No malformed CSV
    """
    response = client.get(
        "/api/audit/export.csv",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Parse CSV
    content = b"".join(response.iter_content()).decode('utf-8')
    reader = csv.reader(StringIO(content))
    
    rows = list(reader)
    assert len(rows) > 1, "CSV should have header + data rows"
    
    # Check header
    expected_headers = [
        "timestamp",
        "tenant_id",
        "user_id",
        "action",
        "txn_id",
        "vendor_normalized",
        "calibrated_p",
        "threshold_used",
        "not_auto_post_reason",
        "cold_start_label_count",
        "ruleset_version_id",
        "model_version_id"
    ]
    
    header = rows[0]
    assert header == expected_headers, f"Header mismatch: {header}"
    
    # Check all rows have correct column count
    expected_col_count = len(expected_headers)
    for i, row in enumerate(rows[1:11]):  # Check first 10 data rows
        assert len(row) == expected_col_count, f"Row {i+1} has {len(row)} columns, expected {expected_col_count}"
    
    print(f"✅ CSV structure validated")
    print(f"   Headers: {len(expected_headers)} columns")
    print(f"   Data rows: {len(rows) - 1}")


def test_timestamps_are_utc_iso8601(db, auth_token, seed_audit_100k):
    """
    Verify timestamps are UTC ISO8601 format.
    
    Checks:
    - Timestamps end with 'Z'
    - Timestamps are parseable as ISO8601
    - No timezone offsets (UTC only)
    """
    response = client.get(
        "/api/audit/export.csv",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    content = b"".join(response.iter_content()).decode('utf-8')
    reader = csv.DictReader(StringIO(content))
    
    timestamps_checked = 0
    for row in reader:
        if timestamps_checked >= 100:  # Check first 100
            break
        
        timestamp = row["timestamp"]
        if not timestamp:  # Skip empty timestamps
            continue
        
        # Check ends with Z
        assert timestamp.endswith("Z"), f"Timestamp not UTC: {timestamp}"
        
        # Check parseable
        try:
            # Remove Z and parse
            dt = datetime.fromisoformat(timestamp[:-1])
            timestamps_checked += 1
        except ValueError as e:
            pytest.fail(f"Timestamp not valid ISO8601: {timestamp} - {e}")
    
    print(f"✅ Timestamps validated (checked {timestamps_checked})")
    print(f"   Format: ISO8601 UTC (ending with Z)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

