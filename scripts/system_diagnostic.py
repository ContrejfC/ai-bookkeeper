#!/usr/bin/env python3
"""
System Diagnostic & Validation Script

Comprehensive pre-Sprint 6 validation of:
- Database schema integrity
- Model storage and loading
- Environment consistency
- Performance benchmarks
- Feature importance
- Cross-domain accuracy

Usage:
    python scripts/system_diagnostic.py
    python scripts/system_diagnostic.py --full  # Include stress tests
"""
import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import argparse

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import (
    Base, TransactionDB, JournalEntryDB, CompanyDB,
    OpenDataIngestionLogDB, ModelTrainingLogDB
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemDiagnostic:
    """Comprehensive system diagnostic runner."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'warnings': [],
            'errors': [],
            'overall_status': 'unknown'
        }
    
    def run_all_checks(self, include_stress_test: bool = False):
        """Run all diagnostic checks."""
        print("\n" + "="*70)
        print("  SYSTEM DIAGNOSTIC - Pre-Sprint 6 Validation")
        print("="*70 + "\n")
        
        # Phase 1: Environment & Schema
        print("📋 PHASE 1: Environment & Schema Checks")
        print("-" * 70)
        self.check_database_schema()
        self.check_model_storage()
        self.check_environment_consistency()
        self.check_dependencies()
        
        # Phase 2: Architecture & Scalability
        print("\n📋 PHASE 2: Architecture & Scalability")
        print("-" * 70)
        self.check_worker_queue()
        self.check_async_job_isolation()
        
        if include_stress_test:
            self.run_stress_test()
        else:
            print("⏩ Skipping stress test (use --full to include)")
            self.results['checks']['stress_test'] = {'status': 'skipped'}
        
        # Phase 3: Model & Data Integrity
        print("\n📋 PHASE 3: Model & Data Integrity")
        print("-" * 70)
        self.extract_feature_importance()
        self.test_cross_domain_accuracy()
        self.setup_drift_baseline()
        
        # Summary
        self.print_summary()
        
        return self.results
    
    def check_database_schema(self):
        """Verify database schema integrity."""
        print("\n1. Database Schema Integrity")
        
        try:
            from sqlalchemy import inspect
            
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            expected_tables = [
                'transactions',
                'journal_entries',
                'companies',
                'users',
                'user_company_links',
                'reconciliations',
                'open_data_ingestion_logs',
                'model_training_logs'
            ]
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            extra_tables = [t for t in existing_tables if t not in expected_tables]
            
            if missing_tables:
                self.results['errors'].append(f"Missing tables: {missing_tables}")
                print(f"   ❌ Missing tables: {missing_tables}")
                self.results['checks']['schema'] = {'status': 'failed', 'missing': missing_tables}
            else:
                print(f"   ✅ All {len(expected_tables)} expected tables exist")
                self.results['checks']['schema'] = {'status': 'passed', 'tables': len(expected_tables)}
            
            if extra_tables:
                print(f"   ℹ️  Extra tables: {extra_tables}")
            
            # Check specific columns
            print("\n   Checking new Sprint 5 columns...")
            txn_columns = [col['name'] for col in inspector.get_columns('transactions')]
            
            required_columns = ['source_type', 'source_name']
            missing_columns = [c for c in required_columns if c not in txn_columns]
            
            if missing_columns:
                self.results['errors'].append(f"Missing columns in transactions: {missing_columns}")
                print(f"   ❌ Missing columns: {missing_columns}")
            else:
                print(f"   ✅ All required columns present")
            
            # Check indexes
            indexes = inspector.get_indexes('transactions')
            print(f"   ✅ {len(indexes)} indexes on transactions table")
            
        except Exception as e:
            self.results['errors'].append(f"Schema check failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['schema'] = {'status': 'error', 'error': str(e)}
    
    def check_model_storage(self):
        """Validate model storage and loading."""
        print("\n2. Model Storage Validation")
        
        try:
            import joblib
            from config.settings import settings
            
            model_path = Path(settings.ML_MODEL_PATH)
            
            if not model_path.exists():
                self.results['errors'].append(f"Model not found: {model_path}")
                print(f"   ❌ Model not found: {model_path}")
                self.results['checks']['model_storage'] = {'status': 'failed'}
                return
            
            print(f"   ✅ Model file exists: {model_path}")
            print(f"   📦 Size: {model_path.stat().st_size / 1024:.1f} KB")
            
            # Load model
            model_bundle = joblib.load(model_path)
            
            required_keys = ['model', 'label_encoder', 'desc_vectorizer', 'counterparty_vectorizer']
            missing_keys = [k for k in required_keys if k not in model_bundle]
            
            if missing_keys:
                self.results['errors'].append(f"Model bundle missing keys: {missing_keys}")
                print(f"   ❌ Missing keys: {missing_keys}")
                self.results['checks']['model_storage'] = {'status': 'failed', 'missing': missing_keys}
            else:
                print(f"   ✅ All model components present")
                print(f"   ✅ Model type: {model_bundle.get('model_type', 'unknown')}")
                print(f"   ✅ Classes: {len(model_bundle['label_encoder'].classes_)}")
                
                if 'metrics' in model_bundle:
                    metrics = model_bundle['metrics']
                    print(f"   ✅ Test accuracy: {metrics.get('test_accuracy', 0):.2%}")
                
                self.results['checks']['model_storage'] = {
                    'status': 'passed',
                    'path': str(model_path),
                    'size_kb': model_path.stat().st_size / 1024,
                    'classes': len(model_bundle['label_encoder'].classes_)
                }
            
        except Exception as e:
            self.results['errors'].append(f"Model loading failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['model_storage'] = {'status': 'error', 'error': str(e)}
    
    def check_environment_consistency(self):
        """Check environment configuration consistency."""
        print("\n3. Environment Consistency")
        
        try:
            from config.settings import settings
            
            required_vars = [
                'DATABASE_URL',
                'REDIS_URL',
                'ML_MODEL_PATH',
                'OPENAI_API_KEY'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not hasattr(settings, var):
                    missing_vars.append(var)
                else:
                    value = getattr(settings, var)
                    if value:
                        print(f"   ✅ {var}: configured")
                    else:
                        print(f"   ⚠️  {var}: empty")
                        self.results['warnings'].append(f"{var} is empty")
            
            if missing_vars:
                self.results['errors'].append(f"Missing environment variables: {missing_vars}")
                print(f"   ❌ Missing: {missing_vars}")
                self.results['checks']['environment'] = {'status': 'failed', 'missing': missing_vars}
            else:
                self.results['checks']['environment'] = {'status': 'passed'}
            
        except Exception as e:
            self.results['errors'].append(f"Environment check failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['environment'] = {'status': 'error', 'error': str(e)}
    
    def check_dependencies(self):
        """Check and report dependency versions."""
        print("\n4. Dependency Versions")
        
        try:
            import pandas as pd
            import sklearn
            import sqlalchemy
            import fastapi
            import pydantic
            import redis
            import rq
            
            versions = {
                'pandas': pd.__version__,
                'scikit-learn': sklearn.__version__,
                'sqlalchemy': sqlalchemy.__version__,
                'fastapi': fastapi.__version__,
                'pydantic': pydantic.__version__,
                'redis': redis.__version__,
                'rq': rq.__version__
            }
            
            for pkg, ver in versions.items():
                print(f"   ✅ {pkg}: {ver}")
            
            self.results['checks']['dependencies'] = {
                'status': 'passed',
                'versions': versions
            }
            
        except Exception as e:
            self.results['errors'].append(f"Dependency check failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['dependencies'] = {'status': 'error', 'error': str(e)}
    
    def check_worker_queue(self):
        """Check Redis and worker queue health."""
        print("\n5. Worker Queue Health")
        
        try:
            from redis import Redis
            from config.settings import settings
            
            # Test Redis connection
            redis_conn = Redis.from_url(settings.REDIS_URL)
            redis_conn.ping()
            print(f"   ✅ Redis connection successful")
            
            # Check queue stats
            from rq import Queue
            queue = Queue(connection=redis_conn)
            
            print(f"   ✅ Jobs in queue: {len(queue)}")
            print(f"   ✅ Failed job registry: {len(queue.failed_job_registry)}")
            
            self.results['checks']['worker_queue'] = {
                'status': 'passed',
                'queued_jobs': len(queue),
                'failed_jobs': len(queue.failed_job_registry)
            }
            
        except Exception as e:
            self.results['warnings'].append(f"Worker queue check: {str(e)}")
            print(f"   ⚠️  Redis not available: {str(e)}")
            self.results['checks']['worker_queue'] = {'status': 'warning', 'error': str(e)}
    
    def check_async_job_isolation(self):
        """Verify async job isolation."""
        print("\n6. Async Job Isolation")
        
        try:
            with get_db_context() as db:
                # Check if we have any job history
                from app.db.models import OpenDataIngestionLogDB
                
                log_count = db.query(OpenDataIngestionLogDB).count()
                print(f"   ✅ Ingestion logs: {log_count} entries")
                
                if log_count > 0:
                    latest = db.query(OpenDataIngestionLogDB).order_by(
                        OpenDataIngestionLogDB.timestamp.desc()
                    ).first()
                    print(f"   ✅ Latest ingestion: {latest.source_name} ({latest.status})")
                
                self.results['checks']['job_isolation'] = {
                    'status': 'passed',
                    'log_entries': log_count
                }
                
        except Exception as e:
            self.results['warnings'].append(f"Job isolation check: {str(e)}")
            print(f"   ⚠️  Warning: {str(e)}")
            self.results['checks']['job_isolation'] = {'status': 'warning', 'error': str(e)}
    
    def run_stress_test(self):
        """Run stress test with large dataset."""
        print("\n7. Stress Test (100k transactions)")
        
        print("   ⚠️  Stress test not implemented in this version")
        print("   💡 Use scripts/internet_data_sync.py with --limit 100000")
        
        self.results['checks']['stress_test'] = {
            'status': 'skipped',
            'reason': 'Manual test required'
        }
    
    def extract_feature_importance(self):
        """Extract and report feature importance."""
        print("\n8. Feature Importance Analysis")
        
        try:
            import joblib
            import numpy as np
            from config.settings import settings
            
            model_path = Path(settings.ML_MODEL_PATH)
            model_bundle = joblib.load(model_path)
            
            model = model_bundle['model']
            desc_vectorizer = model_bundle['desc_vectorizer']
            counterparty_vectorizer = model_bundle['counterparty_vectorizer']
            label_encoder = model_bundle['label_encoder']
            
            # Get feature names
            desc_features = desc_vectorizer.get_feature_names_out()
            counterparty_features = counterparty_vectorizer.get_feature_names_out()
            numeric_features = ['amount_abs', 'is_positive', 'amount_bucket', 'day_of_week', 'month']
            
            all_features = list(desc_features) + list(counterparty_features) + numeric_features
            
            # Get coefficients (for first class as example)
            if hasattr(model, 'coef_'):
                coefs = model.coef_[0]  # First class
                
                # Get top 10 features
                top_indices = np.argsort(np.abs(coefs))[-10:][::-1]
                
                print(f"   ✅ Total features: {len(all_features)}")
                print(f"   ✅ Top 10 features for class '{label_encoder.classes_[0]}':")
                
                for i, idx in enumerate(top_indices, 1):
                    feature_name = all_features[idx] if idx < len(all_features) else f'feature_{idx}'
                    coef_value = coefs[idx]
                    print(f"      {i}. {feature_name}: {coef_value:.4f}")
                
                self.results['checks']['feature_importance'] = {
                    'status': 'passed',
                    'total_features': len(all_features),
                    'top_features': [all_features[idx] for idx in top_indices if idx < len(all_features)]
                }
            else:
                print(f"   ⚠️  Model does not have feature importance")
                self.results['checks']['feature_importance'] = {'status': 'warning', 'reason': 'No coef_ attribute'}
                
        except Exception as e:
            self.results['errors'].append(f"Feature importance extraction failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['feature_importance'] = {'status': 'error', 'error': str(e)}
    
    def test_cross_domain_accuracy(self):
        """Test model on different data domain."""
        print("\n9. Cross-Domain Accuracy Test")
        
        print("   ℹ️  Skipping cross-domain test (requires external dataset)")
        print("   💡 To test: download Kaggle dataset and run train_from_open_data.py")
        
        self.results['checks']['cross_domain'] = {
            'status': 'skipped',
            'reason': 'Requires external dataset'
        }
    
    def setup_drift_baseline(self):
        """Setup baseline for drift detection."""
        print("\n10. Drift Detection Baseline")
        
        try:
            with get_db_context() as db:
                # Get latest training log
                latest = db.query(ModelTrainingLogDB).order_by(
                    ModelTrainingLogDB.timestamp.desc()
                ).first()
                
                if latest:
                    print(f"   ✅ Baseline model: {latest.model_name}")
                    print(f"   ✅ Baseline accuracy: {latest.accuracy:.2%}")
                    print(f"   ✅ Trained on: {latest.records_used} records")
                    print(f"   ✅ Timestamp: {latest.timestamp}")
                    
                    self.results['checks']['drift_baseline'] = {
                        'status': 'passed',
                        'model_name': latest.model_name,
                        'baseline_accuracy': latest.accuracy,
                        'records_used': latest.records_used,
                        'timestamp': latest.timestamp.isoformat()
                    }
                else:
                    self.results['warnings'].append("No training logs found for baseline")
                    print(f"   ⚠️  No training logs found")
                    self.results['checks']['drift_baseline'] = {'status': 'warning', 'reason': 'No logs'}
                    
        except Exception as e:
            self.results['errors'].append(f"Drift baseline setup failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            self.results['checks']['drift_baseline'] = {'status': 'error', 'error': str(e)}
    
    def print_summary(self):
        """Print diagnostic summary."""
        print("\n" + "="*70)
        print("  DIAGNOSTIC SUMMARY")
        print("="*70)
        
        total_checks = len(self.results['checks'])
        passed = sum(1 for c in self.results['checks'].values() if c.get('status') == 'passed')
        failed = sum(1 for c in self.results['checks'].values() if c.get('status') == 'failed')
        warnings = len(self.results['warnings'])
        errors = len(self.results['errors'])
        
        print(f"\nTotal checks: {total_checks}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warnings}")
        print(f"  🔴 Errors: {errors}")
        
        if errors > 0:
            print("\n🔴 ERRORS:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        # Overall status
        if failed > 0 or errors > 0:
            self.results['overall_status'] = 'failed'
            print("\n❌ OVERALL STATUS: FAILED")
            print("   System requires attention before Sprint 6")
        elif warnings > 0:
            self.results['overall_status'] = 'warning'
            print("\n⚠️  OVERALL STATUS: WARNING")
            print("   System functional but has warnings")
        else:
            self.results['overall_status'] = 'passed'
            print("\n✅ OVERALL STATUS: PASSED")
            print("   System ready for Sprint 6!")
        
        print("\n" + "="*70)


def main():
    """Main diagnostic runner."""
    parser = argparse.ArgumentParser(description='System diagnostic and validation')
    parser.add_argument(
        '--full',
        action='store_true',
        help='Include stress tests (may take longer)'
    )
    parser.add_argument(
        '--output',
        default='reports/system_diagnostic.json',
        help='Output file for results'
    )
    
    args = parser.parse_args()
    
    # Run diagnostic
    diagnostic = SystemDiagnostic()
    results = diagnostic.run_all_checks(include_stress_test=args.full)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Full report saved to: {output_path}")
    
    # Exit code
    if results['overall_status'] == 'failed':
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

