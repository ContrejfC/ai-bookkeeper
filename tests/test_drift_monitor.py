"""
Tests for drift monitoring and detection.

Coverage:
- PSI computation with synthetic shifts
- Accuracy drop detection
- OCR confidence drift
- Drift decision logic
- Threshold enforcement
"""
import pytest
import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.drift_monitor import (
    compute_psi,
    compute_js_divergence,
    DriftMonitor
)


class TestPSIComputation:
    """Test Population Stability Index computation."""
    
    def test_psi_no_drift(self):
        """Test PSI with identical distributions."""
        baseline = np.random.normal(100, 15, 1000)
        current = np.random.normal(100, 15, 1000)
        
        psi = compute_psi(baseline, current)
        
        # PSI < 0.10 indicates no significant drift
        assert psi < 0.10, f"PSI={psi:.3f} should indicate no drift"
    
    def test_psi_moderate_drift(self):
        """Test PSI with moderate distribution shift."""
        baseline = np.random.normal(100, 15, 1000)
        current = np.random.normal(110, 15, 1000)  # Mean shifted by 10
        
        psi = compute_psi(baseline, current)
        
        # PSI 0.10-0.25 indicates moderate drift
        assert 0.10 <= psi <= 0.40, f"PSI={psi:.3f} should indicate moderate drift"
    
    def test_psi_significant_drift(self):
        """Test PSI with significant distribution shift."""
        baseline = np.random.normal(100, 15, 1000)
        current = np.random.normal(150, 15, 1000)  # Mean shifted by 50
        
        psi = compute_psi(baseline, current)
        
        # PSI > 0.25 indicates significant drift
        assert psi > 0.25, f"PSI={psi:.3f} should indicate significant drift"
    
    def test_psi_empty_arrays(self):
        """Test PSI with edge cases."""
        baseline = np.array([])
        current = np.array([1, 2, 3])
        
        psi = compute_psi(baseline, current)
        
        # Should handle gracefully
        assert psi == 0.0


class TestJSDivergence:
    """Test Jensen-Shannon divergence computation."""
    
    def test_js_identical_distributions(self):
        """Test JS divergence with identical distributions."""
        p = np.array([0.25, 0.25, 0.25, 0.25])
        q = np.array([0.25, 0.25, 0.25, 0.25])
        
        js = compute_js_divergence(p, q)
        
        assert js < 0.01, f"JS={js:.3f} should be near 0 for identical distributions"
    
    def test_js_different_distributions(self):
        """Test JS divergence with different distributions."""
        p = np.array([0.8, 0.1, 0.05, 0.05])
        q = np.array([0.1, 0.8, 0.05, 0.05])
        
        js = compute_js_divergence(p, q)
        
        assert js > 0.1, f"JS={js:.3f} should indicate difference"


class TestDriftMonitor:
    """Test drift monitor decision logic."""
    
    def test_initialization_with_custom_thresholds(self):
        """Test drift monitor initialization."""
        mock_db = Mock()
        
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.15
        settings.DRIFT_PSI_ALERT = 0.30
        settings.DRIFT_ACC_DROP_PCT = 5.0
        settings.DRIFT_OCR_CONF_Z = 3.0
        settings.DRIFT_MIN_NEW_RECORDS = 2000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 14
        
        monitor = DriftMonitor(mock_db, settings)
        
        assert monitor.psi_warn == 0.15
        assert monitor.psi_alert == 0.30
        assert monitor.acc_drop_pct == 5.0
        assert monitor.ocr_conf_z == 3.0
        assert monitor.min_new_records == 2000
    
    def test_decision_no_drift(self):
        """Test decision when no drift detected."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        # Simulate no drift
        signals = {
            'transaction_classifier': {
                'psi_amount': 0.05,  # Below warn threshold
                'accuracy_drop': 0.01,  # 1pp drop (below 3pp threshold)
                'new_records_since_train': 500,  # Below threshold
                'days_since_train': 3
            },
            'ocr_pipeline': {
                'vendor_conf_z_score': 0.5  # Below 2σ threshold
            },
            'system': {
                'total_records': 1000
            }
        }
        
        decision = monitor.decide(signals)
        
        assert not decision['needs_retrain']
        assert decision['severity'] == 'none'
        assert len(decision['scope']) == 0
    
    def test_decision_psi_alert_triggers_retrain(self):
        """Test that PSI above alert threshold triggers retraining."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        signals = {
            'transaction_classifier': {
                'psi_amount': 0.30,  # Above alert threshold
                'accuracy_drop': 0.01,
                'new_records_since_train': 500,
                'days_since_train': 3
            },
            'ocr_pipeline': {
                'vendor_conf_z_score': 0.5
            },
            'system': {
                'total_records': 1000
            }
        }
        
        decision = monitor.decide(signals)
        
        assert decision['needs_retrain']
        assert decision['severity'] == 'high'
        assert 'txn_classifier' in decision['scope']
        assert any('psi_amount' in r for r in decision['reasons'])
    
    def test_decision_accuracy_drop_triggers_retrain(self):
        """Test that accuracy drop triggers retraining."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        signals = {
            'transaction_classifier': {
                'psi_amount': 0.05,
                'accuracy_drop': 0.05,  # 5pp drop (above 3pp threshold)
                'new_records_since_train': 500,
                'days_since_train': 3
            },
            'ocr_pipeline': {
                'vendor_conf_z_score': 0.5
            },
            'system': {
                'total_records': 1000
            }
        }
        
        decision = monitor.decide(signals)
        
        assert decision['needs_retrain']
        assert decision['severity'] == 'high'
        assert 'txn_classifier' in decision['scope']
        assert any('acc_drop' in r for r in decision['reasons'])
    
    def test_decision_new_records_with_moderate_signal(self):
        """Test that new records + moderate signal triggers retraining."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        signals = {
            'transaction_classifier': {
                'psi_amount': 0.15,  # Moderate (warn threshold)
                'accuracy_drop': 0.01,
                'new_records_since_train': 1500,  # Above threshold
                'days_since_train': 3
            },
            'ocr_pipeline': {
                'vendor_conf_z_score': 0.5
            },
            'system': {
                'total_records': 3000
            }
        }
        
        decision = monitor.decide(signals)
        
        assert decision['needs_retrain']
        assert decision['severity'] == 'medium'
        assert 'txn_classifier' in decision['scope']
    
    def test_decision_ocr_confidence_drift(self):
        """Test OCR confidence drift detection."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        signals = {
            'transaction_classifier': {
                'psi_amount': 0.05,
                'accuracy_drop': 0.01,
                'new_records_since_train': 500,
                'days_since_train': 3
            },
            'ocr_pipeline': {
                'vendor_conf_z_score': 2.5  # Above 2σ threshold
            },
            'system': {
                'total_records': 1000
            }
        }
        
        decision = monitor.decide(signals)
        
        # OCR drift alone doesn't trigger retrain in current logic
        # but it's flagged in reasons
        assert any('ocr_conf_z' in r for r in decision['reasons'])


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_psi_with_constant_values(self):
        """Test PSI when all values are the same."""
        baseline = np.ones(1000) * 100
        current = np.ones(1000) * 100
        
        psi = compute_psi(baseline, current)
        
        # Should handle gracefully (might return 0 or small value)
        assert psi >= 0.0
    
    def test_decision_with_missing_signals(self):
        """Test decision with incomplete signal data."""
        mock_db = Mock()
        settings = Mock()
        settings.DRIFT_PSI_WARN = 0.10
        settings.DRIFT_PSI_ALERT = 0.25
        settings.DRIFT_ACC_DROP_PCT = 3.0
        settings.DRIFT_OCR_CONF_Z = 2.0
        settings.DRIFT_MIN_NEW_RECORDS = 1000
        settings.DRIFT_MIN_DAYS_SINCE_TRAIN = 7
        
        monitor = DriftMonitor(mock_db, settings)
        
        # Minimal signals
        signals = {
            'transaction_classifier': {},
            'ocr_pipeline': {},
            'system': {}
        }
        
        decision = monitor.decide(signals)
        
        # Should not crash, should return conservative decision
        assert 'needs_retrain' in decision
        assert decision['needs_retrain'] == False  # Conservative


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

