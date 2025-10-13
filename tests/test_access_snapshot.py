"""
Tests for Weekly Access Snapshot Job (SOC 2 Min Controls).

Tests:
- CSV file created with correct headers
- JSON file created with expected structure
- PII (emails) are hashed not exposed
- Snapshot includes app users, tenant settings
- Graceful handling when GitHub/Render creds missing
"""
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock

import pytest

from jobs.dump_access_snapshot import (
    hash_email,
    get_app_users,
    get_tenant_settings,
    get_github_org_members,
    generate_snapshot,
    save_snapshot_json,
    save_snapshot_csv,
    main
)


def test_hash_email():
    """Test email hashing for privacy."""
    email = "alice@example.com"
    hashed = hash_email(email)
    
    # Should be hex string (16 chars)
    assert len(hashed) == 16
    assert all(c in "0123456789abcdef" for c in hashed)
    
    # Should be deterministic
    assert hash_email(email) == hashed
    
    # Should be different for different emails
    assert hash_email("bob@example.com") != hashed


@patch('jobs.dump_access_snapshot.get_db_session')
def test_get_app_users(mock_get_session):
    """Test retrieval of app users with tenant assignments."""
    # Mock database
    mock_session = Mock()
    mock_get_session.return_value = iter([mock_session])
    
    # Mock user data
    mock_user = Mock()
    mock_user.user_id = "user-123"
    mock_user.email = "test@example.com"
    mock_user.role = "owner"
    mock_user.is_active = True
    mock_user.created_at = datetime(2025, 1, 1)
    mock_user.last_login_at = None
    
    mock_session.query.return_value.all.return_value = [mock_user]
    mock_session.query.return_value.filter_by.return_value.all.return_value = []
    
    # Test
    users = get_app_users()
    
    assert len(users) == 1
    assert users[0]["user_id"] == "user-123"
    assert users[0]["role"] == "owner"
    assert users[0]["is_active"] is True
    
    # Email should be hashed
    assert users[0]["email_hash"] != "test@example.com"
    assert len(users[0]["email_hash"]) == 16


@patch('jobs.dump_access_snapshot.get_db_session')
def test_get_tenant_settings(mock_get_session):
    """Test retrieval of tenant settings."""
    # Mock database
    mock_session = Mock()
    mock_get_session.return_value = iter([mock_session])
    
    # Mock tenant settings
    mock_setting = Mock()
    mock_setting.tenant_id = "tenant-abc"
    mock_setting.autopost_enabled = False
    mock_setting.autopost_threshold = 0.95
    mock_setting.llm_tenant_cap_usd = 50.0
    mock_setting.updated_at = datetime(2025, 1, 1)
    mock_setting.updated_by = "admin"
    
    mock_session.query.return_value.all.return_value = [mock_setting]
    
    # Test
    settings = get_tenant_settings()
    
    assert len(settings) == 1
    assert settings[0]["tenant_id"] == "tenant-abc"
    assert settings[0]["autopost_enabled"] is False
    assert settings[0]["autopost_threshold"] == 0.95
    assert settings[0]["llm_tenant_cap_usd"] == 50.0


def test_get_github_org_members_no_creds():
    """Test GitHub member fetch gracefully skips when no credentials."""
    # Ensure no credentials
    old_org = os.environ.get("GITHUB_ORG")
    old_token = os.environ.get("GITHUB_TOKEN")
    
    if old_org:
        del os.environ["GITHUB_ORG"]
    if old_token:
        del os.environ["GITHUB_TOKEN"]
    
    try:
        result = get_github_org_members()
        
        # Should return None (not fail)
        assert result is None
    
    finally:
        # Restore
        if old_org:
            os.environ["GITHUB_ORG"] = old_org
        if old_token:
            os.environ["GITHUB_TOKEN"] = old_token


@patch('jobs.dump_access_snapshot.requests.get')
def test_get_github_org_members_with_creds(mock_get):
    """Test GitHub member fetch when credentials available."""
    # Set credentials
    os.environ["GITHUB_ORG"] = "test-org"
    os.environ["GITHUB_TOKEN"] = "test-token"
    
    try:
        # Mock API responses
        mock_members_response = Mock()
        mock_members_response.status_code = 200
        mock_members_response.json.return_value = [
            {"login": "alice", "role": "admin", "site_admin": False}
        ]
        
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "alice",
            "name": "Alice Smith",
            "role": "admin",
            "site_admin": False
        }
        
        mock_get.side_effect = [mock_members_response, mock_user_response]
        
        # Test
        members = get_github_org_members()
        
        assert members is not None
        assert len(members) == 1
        assert members[0]["login"] == "alice"
        assert members[0]["role"] == "admin"
    
    finally:
        # Clean up
        if "GITHUB_ORG" in os.environ:
            del os.environ["GITHUB_ORG"]
        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]


@patch('jobs.dump_access_snapshot.get_tenant_settings')
@patch('jobs.dump_access_snapshot.get_app_users')
@patch('jobs.dump_access_snapshot.get_github_org_members')
@patch('jobs.dump_access_snapshot.get_render_team_members')
def test_generate_snapshot(mock_render, mock_github, mock_users, mock_settings):
    """Test snapshot generation."""
    # Mock data
    mock_users.return_value = [
        {"user_id": "u1", "email_hash": "abc123", "role": "owner", "is_active": True}
    ]
    mock_settings.return_value = [
        {"tenant_id": "t1", "autopost_enabled": False, "autopost_threshold": 0.95}
    ]
    mock_github.return_value = [{"login": "alice", "role": "admin"}]
    mock_render.return_value = None
    
    # Test
    snapshot = generate_snapshot()
    
    # Check structure
    assert "generated_at" in snapshot
    assert "app_users" in snapshot
    assert "tenant_settings" in snapshot
    assert "github_org_members" in snapshot
    assert "render_team_members" in snapshot
    assert "summary" in snapshot
    
    # Check summary
    assert snapshot["summary"]["total_app_users"] == 1
    assert snapshot["summary"]["total_tenants"] == 1


def test_save_snapshot_json(tmp_path):
    """Test JSON snapshot save."""
    snapshot = {
        "generated_at": "2025-01-01T00:00:00Z",
        "app_users": [{"user_id": "u1", "role": "owner"}],
        "summary": {"total_app_users": 1}
    }
    
    # Use temp directory
    import jobs.dump_access_snapshot as module
    old_dir = module.OUTPUT_DIR
    module.OUTPUT_DIR = tmp_path
    
    try:
        output_file = save_snapshot_json(snapshot, "20250101")
        
        # Verify file created
        assert output_file.exists()
        assert output_file.name == "access_snapshot_20250101.json"
        
        # Verify contents
        with open(output_file) as f:
            loaded = json.load(f)
        
        assert loaded["summary"]["total_app_users"] == 1
        assert loaded["generated_at"] == "2025-01-01T00:00:00Z"
    
    finally:
        module.OUTPUT_DIR = old_dir


def test_save_snapshot_csv(tmp_path):
    """Test CSV snapshot save."""
    snapshot = {
        "generated_at": "2025-01-01T00:00:00Z",
        "app_users": [
            {
                "user_id": "u1",
                "email_hash": "abc123",
                "role": "owner",
                "tenant_ids": ["t1"],
                "tenant_count": 1,
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "last_login_at": None
            }
        ],
        "tenant_settings": [
            {
                "tenant_id": "t1",
                "autopost_enabled": False,
                "autopost_threshold": 0.95,
                "llm_tenant_cap_usd": 50.0,
                "updated_at": "2025-01-01T00:00:00Z",
                "updated_by": "admin"
            }
        ],
        "github_org_members": None,
        "render_team_members": None,
        "summary": {}
    }
    
    # Use temp directory
    import jobs.dump_access_snapshot as module
    old_dir = module.OUTPUT_DIR
    module.OUTPUT_DIR = tmp_path
    
    try:
        output_file = save_snapshot_csv(snapshot, "20250101")
        
        # Verify file created
        assert output_file.exists()
        assert output_file.name == "access_snapshot_20250101.csv"
        
        # Verify contents
        with open(output_file, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have rows for users and tenants
        assert len(rows) >= 2
        
        # Check headers present
        assert "section" in rows[0]
        assert "identifier" in rows[0]
        assert "email_hash" in rows[0]
        
        # Check user row
        user_row = [r for r in rows if r["section"] == "app_user"][0]
        assert user_row["identifier"] == "u1"
        assert user_row["email_hash"] == "abc123"
        assert user_row["role"] == "owner"
        
        # Check tenant row
        tenant_row = [r for r in rows if r["section"] == "tenant_setting"][0]
        assert tenant_row["identifier"] == "t1"
    
    finally:
        module.OUTPUT_DIR = old_dir


def test_csv_headers_present(tmp_path):
    """Test CSV has required headers."""
    snapshot = {
        "app_users": [{
            "user_id": "u1",
            "email_hash": "abc",
            "role": "owner",
            "tenant_count": 1,
            "is_active": True,
            "created_at": "2025-01-01",
            "last_login_at": None
        }],
        "tenant_settings": [],
        "github_org_members": None,
        "render_team_members": None,
    }
    
    import jobs.dump_access_snapshot as module
    old_dir = module.OUTPUT_DIR
    module.OUTPUT_DIR = tmp_path
    
    try:
        output_file = save_snapshot_csv(snapshot, "20250101")
        
        with open(output_file, newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        # Required headers
        assert "section" in headers
        assert "identifier" in headers
        assert "email_hash" in headers
        assert "role" in headers
    
    finally:
        module.OUTPUT_DIR = old_dir


def test_no_raw_email_in_output(tmp_path):
    """Test that raw emails are not exposed in outputs."""
    snapshot = {
        "app_users": [{
            "user_id": "u1",
            "email_hash": hash_email("secret@example.com"),
            "role": "owner",
            "tenant_count": 1,
            "is_active": True,
            "created_at": "2025-01-01",
            "last_login_at": None
        }],
        "tenant_settings": [],
        "github_org_members": None,
        "render_team_members": None,
    }
    
    import jobs.dump_access_snapshot as module
    old_dir = module.OUTPUT_DIR
    module.OUTPUT_DIR = tmp_path
    
    try:
        json_file = save_snapshot_json(snapshot, "20250101")
        csv_file = save_snapshot_csv(snapshot, "20250101")
        
        # Check JSON
        json_content = json_file.read_text()
        assert "secret@example.com" not in json_content
        
        # Check CSV
        csv_content = csv_file.read_text()
        assert "secret@example.com" not in csv_content
    
    finally:
        module.OUTPUT_DIR = old_dir

