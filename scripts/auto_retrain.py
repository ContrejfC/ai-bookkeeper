#!/usr/bin/env python3
"""
Auto-Retraining Script

Monitors model performance and triggers retraining when accuracy drops below threshold.

This script checks the latest model performance from ModelTrainingLogDB and:
1. Compares current accuracy against baseline
2. Triggers retraining if accuracy < threshold
3. Logs all retraining events
4. Sends alerts when retraining occurs

Usage:
    python scripts/auto_retrain.py
    python scripts/auto_retrain.py --threshold 0.90  # Custom threshold
    python scripts/auto_retrain.py --dry-run  # Check only, don't retrain
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import ModelTrainingLogDB, TransactionDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoRetrainer:
    """Automated model retraining manager."""
    
    def __init__(self, accuracy_threshold: float = 0.95, dry_run: bool = False):
        self.accuracy_threshold = accuracy_threshold
        self.dry_run = dry_run
        self.retraining_required = False
        self.reason = None
    
    def check_drift(self) -> bool:
        """
        Check if model drift has occurred.
        
        Returns:
            True if retraining is needed, False otherwise
        """
        logger.info("Checking for model drift...")
        
        with get_db_context() as db:
            # Get latest model metrics
            latest_model = db.query(ModelTrainingLogDB).order_by(
                ModelTrainingLogDB.timestamp.desc()
            ).first()
            
            if not latest_model:
                self.reason = "No baseline model found"
                self.retraining_required = True
                logger.warning("No baseline model found - retraining recommended")
                return True
            
            logger.info(f"Latest model: {latest_model.model_name}")
            logger.info(f"  Accuracy: {latest_model.accuracy:.2%}")
            logger.info(f"  Trained on: {latest_model.records_used} records")
            logger.info(f"  Timestamp: {latest_model.timestamp}")
            
            # Check 1: Accuracy below threshold
            if latest_model.accuracy < self.accuracy_threshold:
                self.reason = f"Accuracy {latest_model.accuracy:.2%} < threshold {self.accuracy_threshold:.2%}"
                self.retraining_required = True
                logger.warning(f"❌ {self.reason}")
                return True
            
            # Check 2: Model age (retrain every 30 days)
            age_days = (datetime.now() - latest_model.timestamp).days
            if age_days > 30:
                self.reason = f"Model age {age_days} days > 30 days"
                self.retraining_required = True
                logger.warning(f"⚠️  {self.reason}")
                return True
            
            # Check 3: New data available (>20% growth)
            current_txn_count = db.query(TransactionDB).count()
            growth_rate = (current_txn_count - latest_model.records_used) / latest_model.records_used
            
            if growth_rate > 0.20:
                self.reason = f"Data growth {growth_rate:.1%} > 20%"
                self.retraining_required = True
                logger.warning(f"⚠️  {self.reason}")
                return True
            
            logger.info(f"✅ Model is healthy - no retraining needed")
            logger.info(f"   Age: {age_days} days")
            logger.info(f"   Data growth: {growth_rate:.1%}")
            
            return False
    
    def trigger_retraining(self) -> bool:
        """
        Trigger model retraining.
        
        Returns:
            True if retraining succeeded, False otherwise
        """
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Would retrain model (reason: {self.reason})")
            return True
        
        logger.info(f"🚀 Triggering retraining (reason: {self.reason})...")
        
        try:
            # Run training script
            result = subprocess.run(
                [sys.executable, "scripts/train_from_open_data.py"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Retraining completed successfully")
                
                # Log the retraining event
                self.log_retraining_event("success")
                
                return True
            else:
                logger.error(f"❌ Retraining failed with exit code {result.returncode}")
                logger.error(f"   Error: {result.stderr}")
                
                # Log the failure
                self.log_retraining_event("failed", result.stderr)
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Retraining timeout (>5 minutes)")
            self.log_retraining_event("timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Retraining error: {str(e)}")
            self.log_retraining_event("error", str(e))
            return False
    
    def log_retraining_event(self, status: str, error: str = None):
        """Log retraining event to database."""
        logger.info(f"Logging retraining event (status: {status})...")
        
        # Note: In production, you might create a separate RetrainingLogDB table
        # For now, we just log to stdout
        event = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'reason': self.reason,
            'error': error
        }
        
        logger.info(f"Retraining event: {event}")
    
    def send_alert(self, success: bool):
        """Send alert notification (email, Slack, etc.)."""
        # Placeholder for alerting system
        if success:
            logger.info("📧 Alert: Model retraining completed successfully")
        else:
            logger.error("📧 Alert: Model retraining FAILED - manual intervention required")


def main():
    """Main auto-retraining runner."""
    parser = argparse.ArgumentParser(description='Auto-retraining monitor')
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.95,
        help='Minimum accuracy threshold (default: 0.95)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check only, do not trigger retraining'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  AUTO-RETRAINING MONITOR")
    print("="*70 + "\n")
    
    retrainer = AutoRetrainer(
        accuracy_threshold=args.threshold,
        dry_run=args.dry_run
    )
    
    # Check for drift
    needs_retraining = retrainer.check_drift()
    
    if needs_retraining:
        print("\n⚠️  RETRAINING REQUIRED")
        print(f"   Reason: {retrainer.reason}")
        
        # Trigger retraining
        success = retrainer.trigger_retraining()
        
        # Send alert
        retrainer.send_alert(success)
        
        if success:
            print("\n✅ Retraining completed successfully")
            return 0
        else:
            print("\n❌ Retraining failed - check logs")
            return 1
    else:
        print("\n✅ Model is healthy - no retraining needed")
        return 0


if __name__ == "__main__":
    sys.exit(main())

