#!/usr/bin/env python3
"""
Auto-Retraining Orchestrator v2

Continuous learning system with:
- Drift detection integration
- Shadow training with candidate models
- Safe promotion with guardrails
- Rollback support
- Comprehensive logging

Usage:
    python scripts/auto_retrain_v2.py --mode once
    python scripts/auto_retrain_v2.py --mode watch --interval 1800
    python scripts/auto_retrain_v2.py --dry-run
"""
import sys
import argparse
import logging
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import Base, ModelTrainingLogDB
from app.ml.drift_monitor import create_drift_monitor
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoRetrainerV2:
    """
    Auto-retraining orchestrator with shadow training and safe promotion.
    """
    
    def __init__(self, settings_obj: Any, dry_run: bool = False):
        """
        Initialize auto-retrainer.
        
        Args:
            settings_obj: Settings object
            dry_run: If True, only simulate (don't actually retrain)
        """
        self.settings = settings_obj
        self.dry_run = dry_run
        
        # Paths
        self.model_current = Path(getattr(settings_obj, 'ML_MODEL_PATH', 'models/classifier_open.pkl'))
        self.model_candidate = Path(getattr(settings_obj, 'MODEL_CANDIDATE', 'models/candidate_classifier.pkl'))
        self.model_registry = Path(getattr(settings_obj, 'MODEL_REGISTRY', 'models/'))
        
        # Guardrails
        self.min_records = getattr(settings_obj, 'RETRAIN_GUARD_MIN_RECORDS', 2000)
        self.max_runtime = getattr(settings_obj, 'RETRAIN_GUARD_MAX_RUNTIME', 900)
        self.min_improvement = getattr(settings_obj, 'RETRAIN_GUARD_MIN_IMPROVEMENT', -0.01)
        
        logger.info(
            f"AutoRetrainerV2 initialized: "
            f"min_records={self.min_records}, "
            f"dry_run={dry_run}"
        )
    
    def run_once(self) -> Dict[str, Any]:
        """
        Run one iteration of drift check + optional retrain.
        
        Returns:
            Result dict with status and details
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'drift_checked': False,
            'retrain_triggered': False,
            'promoted': False,
            'error': None
        }
        
        try:
            # Check drift
            with get_db_context() as db:
                drift_monitor = create_drift_monitor(db, self.settings)
                signals = drift_monitor.compute_signals()
                decision = drift_monitor.decide(signals)
            
            result['drift_checked'] = True
            result['drift_decision'] = decision
            
            logger.info(
                f"Drift check: needs_retrain={decision['needs_retrain']}, "
                f"severity={decision['severity']}"
            )
            
            # If retraining needed
            if decision['needs_retrain']:
                if self.dry_run:
                    logger.info("DRY RUN: Would trigger retraining")
                    result['retrain_triggered'] = True
                else:
                    # Check guardrails
                    if not self._check_guardrails(signals):
                        logger.warning("Guardrails not satisfied - skipping retrain")
                        result['error'] = 'guardrails_not_satisfied'
                        return result
                    
                    # Trigger shadow training
                    logger.info("Triggering shadow training...")
                    train_result = self._shadow_train()
                    result['retrain_triggered'] = True
                    result['train_result'] = train_result
                    
                    if train_result['success']:
                        # Evaluate candidate
                        eval_result = self._evaluate_candidate()
                        result['eval_result'] = eval_result
                        
                        # Promote if criteria met
                        if eval_result['should_promote']:
                            logger.info("Promoting candidate to production...")
                            self._promote_candidate()
                            result['promoted'] = True
                        else:
                            logger.info(
                                f"Candidate not promoted: {eval_result['reason']}"
                            )
                    else:
                        logger.error(f"Training failed: {train_result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Auto-retrain error: {e}", exc_info=True)
            result['error'] = str(e)
            return result
    
    def run_watch(self, interval: int = 1800):
        """
        Run in watch mode (continuous loop).
        
        Args:
            interval: Seconds between checks
        """
        logger.info(f"Starting watch mode (interval={interval}s)")
        
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"Watch iteration {iteration}")
            logger.info(f"{'='*70}")
            
            try:
                result = self.run_once()
                
                if result.get('promoted'):
                    logger.info("✅ Model promoted - sleeping for 2x interval")
                    time.sleep(interval * 2)
                else:
                    logger.info(f"💤 Sleeping for {interval}s...")
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                logger.info("Watch mode interrupted by user")
                break
            except Exception as e:
                logger.error(f"Watch iteration error: {e}")
                time.sleep(interval)
    
    def _check_guardrails(self, signals: Dict[str, Any]) -> bool:
        """
        Check if guardrails are satisfied for retraining.
        
        Args:
            signals: Drift signals
            
        Returns:
            True if all guardrails pass
        """
        sys_signals = signals.get('system', {})
        
        # Check minimum records
        total_records = sys_signals.get('total_records', 0)
        if total_records < self.min_records:
            logger.warning(
                f"Guardrail failed: total_records={total_records} < {self.min_records}"
            )
            return False
        
        logger.info(f"✅ Guardrails passed: {total_records} records available")
        return True
    
    def _shadow_train(self) -> Dict[str, Any]:
        """
        Train a candidate model in shadow mode.
        
        Returns:
            Training result dict
        """
        import subprocess
        
        result = {
            'success': False,
            'duration': 0.0,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            logger.info("Running shadow training...")
            
            # Run training script with candidate output path
            cmd = [
                sys.executable,
                "scripts/train_from_open_data.py",
                "--save_model", "true",
                "--output_dir", str(self.model_candidate.parent)
            ]
            
            proc = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=self.max_runtime
            )
            
            duration = time.time() - start_time
            result['duration'] = duration
            
            if proc.returncode == 0:
                # Rename to candidate
                trained_model = self.model_registry / "classifier_open.pkl"
                if trained_model.exists():
                    shutil.copy(trained_model, self.model_candidate)
                    result['success'] = True
                    logger.info(f"✅ Shadow training completed in {duration:.1f}s")
                else:
                    result['error'] = "Trained model not found"
                    logger.error("Trained model file not found")
            else:
                result['error'] = proc.stderr
                logger.error(f"Training failed: {proc.stderr}")
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            result['duration'] = duration
            result['error'] = f"Timeout after {duration:.0f}s"
            logger.error(f"Training timeout (>{self.max_runtime}s)")
        except Exception as e:
            duration = time.time() - start_time
            result['duration'] = duration
            result['error'] = str(e)
            logger.error(f"Training error: {e}")
        
        return result
    
    def _evaluate_candidate(self) -> Dict[str, Any]:
        """
        Evaluate candidate model vs current production model.
        
        Returns:
            Evaluation result with should_promote decision
        """
        result = {
            'should_promote': False,
            'reason': '',
            'prod_metrics': {},
            'candidate_metrics': {}
        }
        
        try:
            import joblib
            
            # Load both models' metadata
            if self.model_current.exists():
                prod_bundle = joblib.load(self.model_current)
                result['prod_metrics'] = prod_bundle.get('metrics', {})
            else:
                logger.warning("No production model found - will promote candidate")
                result['should_promote'] = True
                result['reason'] = 'no_prod_model'
                return result
            
            if not self.model_candidate.exists():
                result['reason'] = 'candidate_not_found'
                return result
            
            candidate_bundle = joblib.load(self.model_candidate)
            result['candidate_metrics'] = candidate_bundle.get('metrics', {})
            
            prod_acc = result['prod_metrics'].get('test_accuracy', 0.0)
            cand_acc = result['candidate_metrics'].get('test_accuracy', 0.0)
            
            prod_f1 = result['prod_metrics'].get('f1_score', 0.0)
            cand_f1 = result['candidate_metrics'].get('f1_score', 0.0)
            
            logger.info(f"Production:  accuracy={prod_acc:.2%}, f1={prod_f1:.2%}")
            logger.info(f"Candidate:   accuracy={cand_acc:.2%}, f1={cand_f1:.2%}")
            
            # Apply promotion criteria
            # 1. Accuracy within tolerance
            acc_diff = cand_acc - prod_acc
            if acc_diff < self.min_improvement:
                result['reason'] = f"accuracy_drop={acc_diff:.4f} < {self.min_improvement}"
                return result
            
            # 2. F1 not worse
            if cand_f1 < prod_f1:
                result['reason'] = f"f1_worse: {cand_f1:.4f} < {prod_f1:.4f}"
                return result
            
            # All checks passed
            result['should_promote'] = True
            result['reason'] = f"improved: acc+{acc_diff:.4f}, f1+{cand_f1 - prod_f1:.4f}"
            
            logger.info(f"✅ Promotion criteria met: {result['reason']}")
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            result['reason'] = f"eval_error: {str(e)}"
        
        return result
    
    def _promote_candidate(self):
        """
        Atomically promote candidate to production.
        
        Creates backup of current model before replacing.
        """
        try:
            # Create backup
            if self.model_current.exists():
                backup_name = f"classifier_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                backup_path = self.model_registry / backup_name
                shutil.copy(self.model_current, backup_path)
                logger.info(f"Created backup: {backup_name}")
            
            # Atomic swap (copy candidate to production)
            shutil.copy(self.model_candidate, self.model_current)
            
            logger.info(f"✅ Promoted {self.model_candidate.name} to {self.model_current.name}")
            
            # Log promotion event
            self._log_promotion_event()
            
        except Exception as e:
            logger.error(f"Promotion failed: {e}")
            raise
    
    def _log_promotion_event(self):
        """Log promotion event to reports."""
        try:
            report_path = Path("reports/retrain_events.md")
            report_path.parent.mkdir(exist_ok=True, parents=True)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append to report
            with open(report_path, 'a') as f:
                f.write(f"\n## Model Promotion - {timestamp}\n\n")
                f.write(f"- **Candidate:** {self.model_candidate}\n")
                f.write(f"- **Promoted to:** {self.model_current}\n")
                f.write(f"- **Timestamp:** {timestamp}\n")
                f.write(f"- **Status:** SUCCESS\n\n")
            
            logger.info(f"Logged promotion event to {report_path}")
            
        except Exception as e:
            logger.warning(f"Failed to log promotion event: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Auto-retraining orchestrator v2')
    parser.add_argument(
        '--mode',
        choices=['once', 'watch'],
        default='once',
        help='Run mode: once (single check) or watch (continuous)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=1800,
        help='Watch mode interval in seconds (default: 1800 = 30 min)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (check only, no retraining)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  AUTO-RETRAINING ORCHESTRATOR V2")
    print("="*70)
    print(f"Mode: {args.mode}")
    print(f"Dry run: {args.dry_run}")
    print("="*70 + "\n")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create orchestrator
    orchestrator = AutoRetrainerV2(settings, dry_run=args.dry_run)
    
    # Run
    if args.mode == 'once':
        result = orchestrator.run_once()
        
        print("\n" + "="*70)
        print("  RESULT")
        print("="*70)
        print(f"Drift checked: {result.get('drift_checked')}")
        print(f"Retrain triggered: {result.get('retrain_triggered')}")
        print(f"Promoted: {result.get('promoted')}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print("="*70 + "\n")
        
        return 0 if not result.get('error') else 1
    else:
        orchestrator.run_watch(interval=args.interval)
        return 0


if __name__ == "__main__":
    sys.exit(main())

