"""
Tests for Data Retention Job (SOC 2 Min Controls).

Tests:
- Dry-run mode doesn't delete files
- Live mode (RETENTION_DELETE=true) deletes eligible files
- Respects retention period (doesn't delete recent files)
- Report generated with correct counts
"""
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

import pytest

from jobs.data_retention import (
    RetentionReport,
    clean_receipts,
    clean_analytics_logs,
    clean_app_logs,
    main
)


def create_old_file(directory: Path, filename: str, days_old: int):
    """Create a file with modified time N days ago."""
    file_path = directory / filename
    file_path.write_text("test content")
    
    # Set modification time
    old_time = (datetime.now() - timedelta(days=days_old)).timestamp()
    os.utime(file_path, (old_time, old_time))
    
    return file_path


def test_retention_report_tracking():
    """Test retention report tracks stats correctly."""
    report = RetentionReport()
    
    report.add_scanned("receipts", 5)
    report.add_eligible("receipts", 2)
    report.add_deleted("receipts", 2)
    
    assert report.results["receipts"]["scanned"] == 5
    assert report.results["receipts"]["eligible"] == 2
    assert report.results["receipts"]["deleted"] == 2
    assert report.results["receipts"]["errors"] == 0


def test_retention_report_errors():
    """Test retention report tracks errors."""
    report = RetentionReport()
    
    report.add_error("receipts", "Failed to delete file.txt")
    
    assert report.results["receipts"]["errors"] == 1
    assert len(report.errors) == 1
    assert "file.txt" in report.errors[0]


def test_retention_report_save(tmp_path):
    """Test retention report saves to file."""
    report = RetentionReport()
    report.add_scanned("receipts", 10)
    report.add_eligible("receipts", 3)
    report.add_deleted("receipts", 3)
    
    output_file = tmp_path / "test_report.txt"
    report.save(output_file)
    
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "DATA RETENTION JOB REPORT" in content
    assert "Scanned: 10" in content
    assert "Eligible for deletion: 3" in content


def test_clean_receipts_dry_run(tmp_path):
    """Test receipts cleaning in dry-run mode (no deletions)."""
    # Create test files
    test_dir = tmp_path / "receipts"
    test_dir.mkdir()
    
    # Old file (should be eligible)
    old_file = create_old_file(test_dir, "old_receipt.pdf", days_old=400)
    
    # Recent file (should not be eligible)
    recent_file = create_old_file(test_dir, "recent_receipt.pdf", days_old=30)
    
    # Mock configuration
    import jobs.data_retention as module
    old_dir = module.RECEIPTS_DIR
    old_delete = module.RETENTION_DELETE
    
    module.RECEIPTS_DIR = test_dir
    module.RETENTION_DELETE = False  # Dry-run
    
    try:
        report = RetentionReport()
        clean_receipts(report)
        
        # Both files should still exist (dry-run)
        assert old_file.exists()
        assert recent_file.exists()
        
        # Check stats
        assert report.results["receipts"]["scanned"] == 2
        assert report.results["receipts"]["eligible"] == 1  # Only old file
        assert report.results["receipts"]["deleted"] == 0  # Dry-run
    
    finally:
        module.RECEIPTS_DIR = old_dir
        module.RETENTION_DELETE = old_delete


def test_clean_receipts_live_mode(tmp_path):
    """Test receipts cleaning in live mode (actually deletes)."""
    # Create test files
    test_dir = tmp_path / "receipts"
    test_dir.mkdir()
    
    # Old file (should be deleted)
    old_file = create_old_file(test_dir, "old_receipt.pdf", days_old=400)
    
    # Recent file (should be kept)
    recent_file = create_old_file(test_dir, "recent_receipt.pdf", days_old=30)
    
    # Mock configuration
    import jobs.data_retention as module
    old_dir = module.RECEIPTS_DIR
    old_delete = module.RETENTION_DELETE
    
    module.RECEIPTS_DIR = test_dir
    module.RETENTION_DELETE = True  # Live mode
    
    try:
        report = RetentionReport()
        clean_receipts(report)
        
        # Old file should be deleted
        assert not old_file.exists()
        
        # Recent file should still exist
        assert recent_file.exists()
        
        # Check stats
        assert report.results["receipts"]["scanned"] == 2
        assert report.results["receipts"]["eligible"] == 1
        assert report.results["receipts"]["deleted"] == 1
    
    finally:
        module.RECEIPTS_DIR = old_dir
        module.RETENTION_DELETE = old_delete


def test_clean_analytics_logs_respects_retention(tmp_path):
    """Test analytics logs cleaning respects retention period."""
    test_dir = tmp_path / "analytics"
    test_dir.mkdir()
    
    # Create files at different ages
    very_old = create_old_file(test_dir, "events_20230101.jsonl", days_old=400)
    old = create_old_file(test_dir, "events_20240601.jsonl", days_old=200)
    recent = create_old_file(test_dir, "events_20251001.jsonl", days_old=30)
    
    # Mock configuration
    import jobs.data_retention as module
    old_dir = module.ANALYTICS_LOGS_DIR
    old_delete = module.RETENTION_DELETE
    old_days = module.RETENTION_DAYS_ANALYTICS
    
    module.ANALYTICS_LOGS_DIR = test_dir
    module.RETENTION_DELETE = True
    module.RETENTION_DAYS_ANALYTICS = 365
    
    try:
        report = RetentionReport()
        clean_analytics_logs(report)
        
        # Very old should be deleted
        assert not very_old.exists()
        
        # Recent should be kept
        assert recent.exists()
        
        # Check eligible count
        assert report.results["analytics_logs"]["eligible"] >= 1
    
    finally:
        module.ANALYTICS_LOGS_DIR = old_dir
        module.RETENTION_DELETE = old_delete
        module.RETENTION_DAYS_ANALYTICS = old_days


def test_clean_app_logs(tmp_path):
    """Test application logs cleaning."""
    test_dir = tmp_path / "logs"
    test_dir.mkdir()
    
    # Old log file (should be deleted)
    old_log = create_old_file(test_dir, "app.log.2024-01-01", days_old=60)
    
    # Recent log file (should be kept)
    recent_log = create_old_file(test_dir, "app.log", days_old=5)
    
    # Mock configuration
    import jobs.data_retention as module
    old_dir = module.APP_LOGS_DIR
    old_delete = module.RETENTION_DELETE
    old_days = module.RETENTION_DAYS_LOGS
    
    module.APP_LOGS_DIR = test_dir
    module.RETENTION_DELETE = True
    module.RETENTION_DAYS_LOGS = 30
    
    try:
        report = RetentionReport()
        clean_app_logs(report)
        
        # Old log should be deleted
        assert not old_log.exists()
        
        # Recent log should be kept
        assert recent_log.exists()
        
        # Check stats
        assert report.results["app_logs"]["eligible"] == 1
        assert report.results["app_logs"]["deleted"] == 1
    
    finally:
        module.APP_LOGS_DIR = old_dir
        module.RETENTION_DELETE = old_delete
        module.RETENTION_DAYS_LOGS = old_days


def test_retention_job_graceful_on_missing_dirs():
    """Test retention job handles missing directories gracefully."""
    # Mock configuration to point to non-existent directories
    import jobs.data_retention as module
    old_receipts_dir = module.RECEIPTS_DIR
    old_analytics_dir = module.ANALYTICS_LOGS_DIR
    old_logs_dir = module.APP_LOGS_DIR
    
    module.RECEIPTS_DIR = Path("/tmp/nonexistent_receipts")
    module.ANALYTICS_LOGS_DIR = Path("/tmp/nonexistent_analytics")
    module.APP_LOGS_DIR = Path("/tmp/nonexistent_logs")
    
    try:
        report = RetentionReport()
        
        # Should not raise exceptions
        clean_receipts(report)
        clean_analytics_logs(report)
        clean_app_logs(report)
        
        # Should have zero scanned files
        assert report.results["receipts"]["scanned"] == 0
        assert report.results["analytics_logs"]["scanned"] == 0
        assert report.results["app_logs"]["scanned"] == 0
    
    finally:
        module.RECEIPTS_DIR = old_receipts_dir
        module.ANALYTICS_LOGS_DIR = old_analytics_dir
        module.APP_LOGS_DIR = old_logs_dir


def test_dry_run_flag_from_environment():
    """Test dry-run flag reads from RETENTION_DELETE environment."""
    # Test default (dry-run)
    old_val = os.environ.get("RETENTION_DELETE")
    if old_val:
        del os.environ["RETENTION_DELETE"]
    
    try:
        # Re-import to pick up env change
        import importlib
        import jobs.data_retention as module
        importlib.reload(module)
        
        assert module.RETENTION_DELETE is False
        
        # Test live mode
        os.environ["RETENTION_DELETE"] = "true"
        importlib.reload(module)
        
        assert module.RETENTION_DELETE is True
    
    finally:
        if old_val:
            os.environ["RETENTION_DELETE"] = old_val
        elif "RETENTION_DELETE" in os.environ:
            del os.environ["RETENTION_DELETE"]


def test_retention_report_dry_run_warning(tmp_path):
    """Test report includes dry-run warning when applicable."""
    report = RetentionReport()
    report.add_scanned("receipts", 5)
    report.add_eligible("receipts", 2)
    # No deletions (dry-run)
    
    output_file = tmp_path / "test_report.txt"
    report.save(output_file)
    
    content = output_file.read_text()
    assert "DRY-RUN MODE" in content
    assert "No files were actually deleted" in content

