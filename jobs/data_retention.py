#!/usr/bin/env python3
"""
Data Retention Job (SOC 2 Min Controls).

Deletes old files/records according to retention policy:
- Receipt files: 365 days (default)
- Analytics logs: 365 days (default)
- Application logs: 30 days (default)

Safety: Dry-run by default. Set RETENTION_DELETE=true to actually delete.

Environment:
- RETENTION_DAYS_RECEIPTS: Days to retain receipt files (default=365)
- RETENTION_DAYS_ANALYTICS: Days to retain analytics logs (default=365)
- RETENTION_DAYS_LOGS: Days to retain application logs (default=30)
- RETENTION_DELETE: Set to 'true' to actually delete (default=false, dry-run)

Outputs:
- reports/compliance/data_retention_<date>.txt (deletion report)

Usage:
    python jobs/data_retention.py               # Dry-run
    RETENTION_DELETE=true python jobs/data_retention.py  # Live run
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ops.logging import get_logger

logger = get_logger(__name__)

# Configuration from environment
RETENTION_DAYS_RECEIPTS = int(os.getenv("RETENTION_DAYS_RECEIPTS", "365"))
RETENTION_DAYS_ANALYTICS = int(os.getenv("RETENTION_DAYS_ANALYTICS", "365"))
RETENTION_DAYS_LOGS = int(os.getenv("RETENTION_DAYS_LOGS", "30"))
RETENTION_DELETE = os.getenv("RETENTION_DELETE", "false").lower() == "true"

# Output directory
OUTPUT_DIR = Path("reports/compliance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Data directories
RECEIPTS_DIR = Path("data/receipts")
ANALYTICS_LOGS_DIR = Path("logs/analytics")
APP_LOGS_DIR = Path("logs")


class RetentionReport:
    """Retention job report."""
    
    def __init__(self):
        self.dry_run = not RETENTION_DELETE
        self.results = {
            "receipts": {"scanned": 0, "eligible": 0, "deleted": 0, "errors": 0},
            "analytics_logs": {"scanned": 0, "eligible": 0, "deleted": 0, "errors": 0},
            "app_logs": {"scanned": 0, "eligible": 0, "deleted": 0, "errors": 0},
        }
        self.errors = []
    
    def add_scanned(self, category: str, count: int = 1):
        """Record files scanned."""
        self.results[category]["scanned"] += count
    
    def add_eligible(self, category: str, count: int = 1):
        """Record files eligible for deletion."""
        self.results[category]["eligible"] += count
    
    def add_deleted(self, category: str, count: int = 1):
        """Record files deleted."""
        self.results[category]["deleted"] += count
    
    def add_error(self, category: str, error: str, count: int = 1):
        """Record deletion error."""
        self.results[category]["errors"] += count
        self.errors.append(f"[{category}] {error}")
    
    def save(self, output_file: Path):
        """Save report to file."""
        with open(output_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("DATA RETENTION JOB REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Mode: {'DRY-RUN (no deletions)' if self.dry_run else 'LIVE (deletions enabled)'}\n\n")
            
            f.write("Retention Policy:\n")
            f.write(f"  - Receipts: {RETENTION_DAYS_RECEIPTS} days\n")
            f.write(f"  - Analytics logs: {RETENTION_DAYS_ANALYTICS} days\n")
            f.write(f"  - Application logs: {RETENTION_DAYS_LOGS} days\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("RESULTS\n")
            f.write("-" * 60 + "\n\n")
            
            for category, stats in self.results.items():
                f.write(f"{category.upper().replace('_', ' ')}:\n")
                f.write(f"  Scanned: {stats['scanned']}\n")
                f.write(f"  Eligible for deletion: {stats['eligible']}\n")
                f.write(f"  Deleted: {stats['deleted']}\n")
                f.write(f"  Errors: {stats['errors']}\n\n")
            
            if self.errors:
                f.write("-" * 60 + "\n")
                f.write("ERRORS\n")
                f.write("-" * 60 + "\n\n")
                for error in self.errors:
                    f.write(f"  {error}\n")
                f.write("\n")
            
            f.write("-" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 60 + "\n\n")
            
            total_scanned = sum(s["scanned"] for s in self.results.values())
            total_eligible = sum(s["eligible"] for s in self.results.values())
            total_deleted = sum(s["deleted"] for s in self.results.values())
            total_errors = sum(s["errors"] for s in self.results.values())
            
            f.write(f"Total scanned: {total_scanned}\n")
            f.write(f"Total eligible: {total_eligible}\n")
            f.write(f"Total deleted: {total_deleted}\n")
            f.write(f"Total errors: {total_errors}\n\n")
            
            if self.dry_run and total_eligible > 0:
                f.write("⚠️  DRY-RUN MODE: No files were actually deleted.\n")
                f.write("    Set RETENTION_DELETE=true to enable deletions.\n\n")
            elif total_deleted > 0:
                f.write("✓ Deletions completed successfully.\n\n")
            else:
                f.write("✓ No files required deletion.\n\n")


def clean_receipts(report: RetentionReport):
    """Clean old receipt files."""
    logger.info(f"Scanning receipts directory: {RECEIPTS_DIR}")
    
    if not RECEIPTS_DIR.exists():
        logger.warning(f"Receipts directory not found: {RECEIPTS_DIR}")
        return
    
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS_RECEIPTS)
    logger.info(f"Retention cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Scan all files
    for file_path in RECEIPTS_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        
        report.add_scanned("receipts")
        
        # Check file age
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_mtime < cutoff_date:
            report.add_eligible("receipts")
            
            if RETENTION_DELETE:
                try:
                    file_path.unlink()
                    report.add_deleted("receipts")
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    report.add_error("receipts", f"Failed to delete {file_path}: {e}")
                    logger.error(f"Error deleting {file_path}: {e}")
            else:
                logger.debug(f"[DRY-RUN] Would delete: {file_path}")
    
    logger.info(f"Receipts scan complete: {report.results['receipts']}")


def clean_analytics_logs(report: RetentionReport):
    """Clean old analytics log files."""
    logger.info(f"Scanning analytics logs directory: {ANALYTICS_LOGS_DIR}")
    
    if not ANALYTICS_LOGS_DIR.exists():
        logger.warning(f"Analytics logs directory not found: {ANALYTICS_LOGS_DIR}")
        return
    
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS_ANALYTICS)
    logger.info(f"Retention cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Scan all .jsonl files
    for file_path in ANALYTICS_LOGS_DIR.glob("*.jsonl"):
        report.add_scanned("analytics_logs")
        
        # Check file age
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_mtime < cutoff_date:
            report.add_eligible("analytics_logs")
            
            if RETENTION_DELETE:
                try:
                    file_path.unlink()
                    report.add_deleted("analytics_logs")
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    report.add_error("analytics_logs", f"Failed to delete {file_path}: {e}")
                    logger.error(f"Error deleting {file_path}: {e}")
            else:
                logger.debug(f"[DRY-RUN] Would delete: {file_path}")
    
    logger.info(f"Analytics logs scan complete: {report.results['analytics_logs']}")


def clean_app_logs(report: RetentionReport):
    """Clean old application log files."""
    logger.info(f"Scanning application logs directory: {APP_LOGS_DIR}")
    
    if not APP_LOGS_DIR.exists():
        logger.warning(f"Application logs directory not found: {APP_LOGS_DIR}")
        return
    
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS_LOGS)
    logger.info(f"Retention cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Scan log files (exclude analytics subdirectory)
    for file_path in APP_LOGS_DIR.glob("*.log"):
        report.add_scanned("app_logs")
        
        # Check file age
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_mtime < cutoff_date:
            report.add_eligible("app_logs")
            
            if RETENTION_DELETE:
                try:
                    file_path.unlink()
                    report.add_deleted("app_logs")
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    report.add_error("app_logs", f"Failed to delete {file_path}: {e}")
                    logger.error(f"Error deleting {file_path}: {e}")
            else:
                logger.debug(f"[DRY-RUN] Would delete: {file_path}")
    
    logger.info(f"Application logs scan complete: {report.results['app_logs']}")


def main():
    """Main entry point."""
    logger.info("=== Data Retention Job Started ===")
    
    if RETENTION_DELETE:
        logger.warning("⚠️  LIVE MODE: Deletions are ENABLED")
    else:
        logger.info("ℹ️  DRY-RUN MODE: No files will be deleted")
    
    report = RetentionReport()
    
    try:
        # Clean each category
        clean_receipts(report)
        clean_analytics_logs(report)
        clean_app_logs(report)
        
        # Save report
        date_str = datetime.utcnow().strftime("%Y%m%d")
        output_file = OUTPUT_DIR / f"data_retention_{date_str}.txt"
        report.save(output_file)
        
        logger.info(f"Report saved: {output_file}")
        logger.info("=== Data Retention Job Completed ===")
        
        # Print summary
        print(f"\n✓ Data retention job completed")
        print(f"✓ Report: {output_file}")
        
        total_eligible = sum(s["eligible"] for s in report.results.values())
        total_deleted = sum(s["deleted"] for s in report.results.values())
        
        if report.dry_run and total_eligible > 0:
            print(f"\n⚠️  DRY-RUN: {total_eligible} files eligible for deletion (not deleted)")
            print("   Set RETENTION_DELETE=true to enable deletions")
        elif total_deleted > 0:
            print(f"\n✓ Deleted {total_deleted} files")
        else:
            print("\n✓ No files required deletion")
        
        return 0
    
    except Exception as e:
        logger.error(f"Data retention job failed: {e}", exc_info=True)
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

