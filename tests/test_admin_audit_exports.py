"""
Tests for Admin Audit Exports API (SOC 2 Min Controls).

Tests:
- Owner can export audit logs (JSONL and CSV)
- Staff gets 403 Forbidden
- Streaming responses work correctly
- CSV has correct headers
- Date range filtering works
"""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.api.admin_compliance import router
from app.ui.rbac import Role, User


# Create test app with just the compliance router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

client = TestClient(app)


def mock_owner_user():
    """Create a mock owner user."""
    return User(
        user_id="user-owner-001",
        email="owner@example.com",
        role=Role.OWNER,
        assigned_tenant_ids=[]
    )


def mock_staff_user():
    """Create a mock staff user."""
    return User(
        user_id="user-staff-001",
        email="staff@example.com",
        role=Role.STAFF,
        assigned_tenant_ids=["tenant-1"]
    )


def mock_audit_logs():
    """Create mock audit log records."""
    logs = []
    for i in range(5):
        mock_log = Mock()
        mock_log.id = i + 1
        mock_log.timestamp = datetime.utcnow() - timedelta(days=i)
        mock_log.tenant_id = "tenant-test"
        mock_log.txn_id = f"txn-{i}"
        mock_log.vendor_normalized = "VENDOR_ABC"
        mock_log.action = "reviewed"
        mock_log.not_auto_post_reason = "below_threshold"
        mock_log.calibrated_p = 0.85
        mock_log.threshold_used = 0.90
        mock_log.user_id = "user-123"
        mock_log.cold_start_label_count = None
        mock_log.cold_start_eligible = None
        logs.append(mock_log)
    return logs


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
@patch('app.api.admin_compliance.get_decision_audit_logs')
def test_export_audit_jsonl_owner(mock_get_logs, mock_get_db, mock_get_user):
    """Test owner can export audit logs as JSONL."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Mock audit logs
    mock_get_logs.return_value = iter(mock_audit_logs())
    
    # Test
    response = client.get("/api/admin/audit/export.jsonl")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-ndjson"
    assert "audit_export_" in response.headers["content-disposition"]
    
    # Parse JSONL
    lines = response.text.strip().split("\n")
    assert len(lines) == 5  # 5 mock records
    
    # Check first line is valid JSON
    import json
    first_record = json.loads(lines[0])
    assert "id" in first_record
    assert "timestamp" in first_record
    assert "tenant_id" in first_record


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
def test_export_audit_jsonl_staff_forbidden(mock_get_db, mock_get_user):
    """Test staff user gets 403 Forbidden."""
    # Mock staff user
    mock_get_user.return_value = mock_staff_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Test
    response = client.get("/api/admin/audit/export.jsonl")
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
@patch('app.api.admin_compliance.get_decision_audit_logs')
def test_export_audit_csv_owner(mock_get_logs, mock_get_db, mock_get_user):
    """Test owner can export audit logs as CSV."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Mock audit logs
    mock_get_logs.return_value = iter(mock_audit_logs())
    
    # Test
    response = client.get("/api/admin/audit/export.csv")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "audit_export_" in response.headers["content-disposition"]
    
    # Parse CSV
    import csv
    from io import StringIO
    
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    rows = list(reader)
    
    assert len(rows) == 5  # 5 mock records
    
    # Check headers
    assert "id" in reader.fieldnames
    assert "timestamp" in reader.fieldnames
    assert "tenant_id" in reader.fieldnames
    assert "action" in reader.fieldnames


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
def test_export_audit_csv_staff_forbidden(mock_get_db, mock_get_user):
    """Test staff user gets 403 Forbidden for CSV export."""
    # Mock staff user
    mock_get_user.return_value = mock_staff_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Test
    response = client.get("/api/admin/audit/export.csv")
    
    assert response.status_code == 403


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
@patch('app.api.admin_compliance.get_decision_audit_logs')
def test_export_audit_custom_days(mock_get_logs, mock_get_db, mock_get_user):
    """Test custom date range parameter."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Mock audit logs
    mock_get_logs.return_value = iter([])
    
    # Test with custom days
    response = client.get("/api/admin/audit/export.jsonl?days=30")
    
    assert response.status_code == 200
    
    # Verify days parameter was passed
    mock_get_logs.assert_called_once()
    args, kwargs = mock_get_logs.call_args
    assert args[1] == 30  # days parameter


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
def test_export_audit_invalid_days(mock_get_db, mock_get_user):
    """Test validation of days parameter."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Test with days too large
    response = client.get("/api/admin/audit/export.jsonl?days=999")
    assert response.status_code == 400
    assert "between 1 and 365" in response.json()["detail"]
    
    # Test with days too small
    response = client.get("/api/admin/audit/export.jsonl?days=0")
    assert response.status_code == 400


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
def test_get_compliance_status_owner(mock_get_db, mock_get_user):
    """Test owner can get compliance status."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Test
    response = client.get("/api/admin/compliance/status")
    
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert "timestamp" in data
    assert "evidence" in data
    assert "pr_gate" in data
    assert "logging" in data
    
    # Check evidence structure
    assert "access_snapshot" in data["evidence"]
    assert "backup_restore" in data["evidence"]
    assert "data_retention" in data["evidence"]


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
def test_get_compliance_status_staff_forbidden(mock_get_db, mock_get_user):
    """Test staff user gets 403 Forbidden for compliance status."""
    # Mock staff user
    mock_get_user.return_value = mock_staff_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Test
    response = client.get("/api/admin/compliance/status")
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
@patch('app.api.admin_compliance.get_decision_audit_logs')
def test_csv_export_has_all_fields(mock_get_logs, mock_get_db, mock_get_user):
    """Test CSV export includes all required fields."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Mock audit logs
    mock_get_logs.return_value = iter(mock_audit_logs())
    
    # Test
    response = client.get("/api/admin/audit/export.csv")
    
    # Parse CSV
    import csv
    from io import StringIO
    
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    # Check all expected fields are present
    expected_fields = [
        "id", "timestamp", "tenant_id", "txn_id", "vendor_normalized",
        "action", "not_auto_post_reason", "calibrated_p", "threshold_used",
        "user_id", "cold_start_label_count", "cold_start_eligible"
    ]
    
    for field in expected_fields:
        assert field in reader.fieldnames, f"Missing field: {field}"


@patch('app.api.admin_compliance.get_current_user')
@patch('app.api.admin_compliance.get_db')
@patch('app.api.admin_compliance.get_decision_audit_logs')
def test_jsonl_export_one_line_per_record(mock_get_logs, mock_get_db, mock_get_user):
    """Test JSONL export has one JSON object per line."""
    # Mock user
    mock_get_user.return_value = mock_owner_user()
    
    # Mock database
    mock_session = Mock()
    mock_get_db.return_value = mock_session
    
    # Mock 3 audit logs
    mock_get_logs.return_value = iter(mock_audit_logs()[:3])
    
    # Test
    response = client.get("/api/admin/audit/export.jsonl")
    
    lines = response.text.strip().split("\n")
    assert len(lines) == 3
    
    # Each line should be valid JSON
    import json
    for line in lines:
        obj = json.loads(line)
        assert isinstance(obj, dict)
        assert "id" in obj

