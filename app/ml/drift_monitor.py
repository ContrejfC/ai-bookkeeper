"""
Drift Monitor for Transaction Classifier and OCR Pipeline

Detects data drift and performance drift across:
- Transaction classifier (TF-IDF, MCC, amount bins, temporal features)
- OCR extraction fields (confidence distributions)

Emits drift decisions with reasons for auto-retraining.
"""
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def compute_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Compute Population Stability Index (PSI) between two distributions.
    
    PSI measures the shift in distribution between two populations.
    PSI < 0.10: No significant change
    PSI 0.10-0.25: Moderate change, investigate
    PSI > 0.25: Significant change, likely drift
    
    Args:
        expected: Baseline distribution (historical)
        actual: Current distribution
        bins: Number of bins for bucketing
        
    Returns:
        PSI score (0 = no drift, higher = more drift)
    """
    # Handle edge cases
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    
    # Create bins based on expected distribution
    try:
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)  # Remove duplicates
    except:
        return 0.0
    
    if len(breakpoints) < 2:
        return 0.0
    
    # Bin both distributions
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)
    
    # Convert to percentages
    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)
    
    # Avoid division by zero
    expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
    actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)
    
    # Compute PSI
    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    
    return float(psi)


def compute_js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """
    Compute Jensen-Shannon divergence between two probability distributions.
    
    JS divergence is symmetric and bounded [0, 1].
    
    Args:
        p: First probability distribution
        q: Second probability distribution
        
    Returns:
        JS divergence (0 = identical, 1 = completely different)
    """
    if len(p) == 0 or len(q) == 0:
        return 0.0
    
    # Normalize to probabilities
    p = p / np.sum(p)
    q = q / np.sum(q)
    
    # Compute M = (P + Q) / 2
    m = (p + q) / 2
    
    # Avoid log(0)
    p = np.where(p == 0, 1e-10, p)
    q = np.where(q == 0, 1e-10, q)
    m = np.where(m == 0, 1e-10, m)
    
    # Compute KL divergences
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    
    # JS divergence = (KL(P||M) + KL(Q||M)) / 2
    js = (kl_pm + kl_qm) / 2
    
    # Normalize to [0, 1]
    js = np.sqrt(js)
    
    return float(min(js, 1.0))


class DriftMonitor:
    """
    Monitors data and performance drift for ML models.
    
    Tracks:
    - Transaction classifier: Feature drift (PSI), accuracy drops
    - OCR pipeline: Confidence distributions, extraction rates
    """
    
    def __init__(self, db_session: Any, settings: Any):
        """
        Initialize drift monitor.
        
        Args:
            db_session: Database session
            settings: Settings object with drift thresholds
        """
        self.db = db_session
        self.settings = settings
        
        # Thresholds
        self.psi_warn = getattr(settings, 'DRIFT_PSI_WARN', 0.10)
        self.psi_alert = getattr(settings, 'DRIFT_PSI_ALERT', 0.25)
        self.acc_drop_pct = getattr(settings, 'DRIFT_ACC_DROP_PCT', 3.0)
        self.ocr_conf_z = getattr(settings, 'DRIFT_OCR_CONF_Z', 2.0)
        self.min_new_records = getattr(settings, 'DRIFT_MIN_NEW_RECORDS', 1000)
        self.min_days_since_train = getattr(settings, 'DRIFT_MIN_DAYS_SINCE_TRAIN', 7)
        
        logger.info(
            f"DriftMonitor initialized: PSI alert={self.psi_alert}, "
            f"acc_drop={self.acc_drop_pct}pp, ocr_z={self.ocr_conf_z}"
        )
    
    def compute_signals(self) -> Dict[str, Any]:
        """
        Compute all drift signals.
        
        Returns:
            Dict with drift signals for various metrics
        """
        signals = {
            'timestamp': datetime.now().isoformat(),
            'transaction_classifier': {},
            'ocr_pipeline': {},
            'system': {}
        }
        
        # Transaction classifier signals
        signals['transaction_classifier'] = self._compute_txn_classifier_signals()
        
        # OCR pipeline signals
        signals['ocr_pipeline'] = self._compute_ocr_signals()
        
        # System-level signals
        signals['system'] = self._compute_system_signals()
        
        return signals
    
    def _compute_txn_classifier_signals(self) -> Dict[str, Any]:
        """Compute drift signals for transaction classifier."""
        from app.db.models import TransactionDB, ModelTrainingLogDB
        
        signals = {
            'psi_amount': 0.0,
            'accuracy_baseline': 0.0,
            'accuracy_current': 0.0,
            'accuracy_drop': 0.0,
            'new_records_since_train': 0,
            'days_since_train': 0
        }
        
        try:
            # Get baseline model
            baseline_model = self.db.query(ModelTrainingLogDB).order_by(
                ModelTrainingLogDB.timestamp.desc()
            ).first()
            
            if not baseline_model:
                logger.warning("No baseline model found")
                return signals
            
            signals['accuracy_baseline'] = baseline_model.accuracy
            signals['days_since_train'] = (datetime.now() - baseline_model.timestamp).days
            
            # Get new records since training
            new_records = self.db.query(TransactionDB).filter(
                TransactionDB.created_at > baseline_model.timestamp
            ).count()
            
            signals['new_records_since_train'] = new_records
            
            # Compute PSI for amount distribution
            # Get baseline amounts
            baseline_txns = self.db.query(TransactionDB).filter(
                TransactionDB.created_at <= baseline_model.timestamp
            ).limit(5000).all()
            
            recent_txns = self.db.query(TransactionDB).filter(
                TransactionDB.created_at > baseline_model.timestamp
            ).limit(5000).all()
            
            if baseline_txns and recent_txns:
                baseline_amounts = np.array([abs(t.amount) for t in baseline_txns])
                recent_amounts = np.array([abs(t.amount) for t in recent_txns])
                
                signals['psi_amount'] = compute_psi(baseline_amounts, recent_amounts)
            
            # Estimate current accuracy (simplified - in production, use validation set)
            # For now, use baseline accuracy (would need labeled validation data)
            signals['accuracy_current'] = baseline_model.accuracy
            signals['accuracy_drop'] = signals['accuracy_baseline'] - signals['accuracy_current']
            
        except Exception as e:
            logger.error(f"Error computing classifier signals: {e}")
        
        return signals
    
    def _compute_ocr_signals(self) -> Dict[str, Any]:
        """Compute drift signals for OCR pipeline."""
        signals = {
            'vendor_conf_mean': 0.0,
            'vendor_conf_std': 0.0,
            'vendor_conf_z_score': 0.0,
            'amount_conf_mean': 0.0,
            'date_conf_mean': 0.0,
            'extraction_rate': 0.0
        }
        
        # TODO: In production, track OCR results in a dedicated table
        # For now, return placeholder values
        logger.debug("OCR drift signals: Using placeholder values")
        
        return signals
    
    def _compute_system_signals(self) -> Dict[str, Any]:
        """Compute system-level signals."""
        from app.db.models import TransactionDB
        
        signals = {
            'total_records': 0,
            'records_last_7d': 0,
            'records_last_30d': 0
        }
        
        try:
            signals['total_records'] = self.db.query(TransactionDB).count()
            
            seven_days_ago = datetime.now() - timedelta(days=7)
            signals['records_last_7d'] = self.db.query(TransactionDB).filter(
                TransactionDB.created_at >= seven_days_ago
            ).count()
            
            thirty_days_ago = datetime.now() - timedelta(days=30)
            signals['records_last_30d'] = self.db.query(TransactionDB).filter(
                TransactionDB.created_at >= thirty_days_ago
            ).count()
            
        except Exception as e:
            logger.error(f"Error computing system signals: {e}")
        
        return signals
    
    def decide(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make retraining decision based on signals.
        
        Args:
            signals: Drift signals from compute_signals()
            
        Returns:
            Decision dict with needs_retrain flag and reasons
        """
        decision = {
            'timestamp': datetime.now().isoformat(),
            'needs_retrain': False,
            'reasons': [],
            'scope': [],
            'severity': 'none',  # none, low, medium, high
            'signals': signals
        }
        
        txn_signals = signals.get('transaction_classifier', {})
        ocr_signals = signals.get('ocr_pipeline', {})
        sys_signals = signals.get('system', {})
        
        # Check transaction classifier drift
        reasons = []
        scope = []
        
        # PSI check
        psi_amount = txn_signals.get('psi_amount', 0.0)
        if psi_amount >= self.psi_alert:
            reasons.append(f"psi_amount={psi_amount:.3f} >= {self.psi_alert} (ALERT)")
            scope.append('txn_classifier')
        elif psi_amount >= self.psi_warn:
            reasons.append(f"psi_amount={psi_amount:.3f} >= {self.psi_warn} (WARN)")
        
        # Accuracy drop check
        acc_drop = txn_signals.get('accuracy_drop', 0.0) * 100  # Convert to percentage points
        if acc_drop >= self.acc_drop_pct:
            reasons.append(f"acc_drop={acc_drop:.1f}pp >= {self.acc_drop_pct}pp")
            scope.append('txn_classifier')
        
        # Time since training check
        days_since_train = txn_signals.get('days_since_train', 0)
        if days_since_train >= self.min_days_since_train * 2:  # 2x threshold
            reasons.append(f"days_since_train={days_since_train} >= {self.min_days_since_train * 2}")
            scope.append('txn_classifier')
        
        # New records check
        new_records = txn_signals.get('new_records_since_train', 0)
        if new_records >= self.min_new_records:
            reasons.append(f"new_records={new_records} >= {self.min_new_records}")
            if 'txn_classifier' not in scope:
                scope.append('txn_classifier')
        
        # OCR confidence drift check
        ocr_conf_z = ocr_signals.get('vendor_conf_z_score', 0.0)
        if abs(ocr_conf_z) >= self.ocr_conf_z:
            reasons.append(f"ocr_conf_z={ocr_conf_z:.2f} >= {self.ocr_conf_z}σ")
            scope.append('ocr_extractor')
        
        # Determine severity
        severity = 'none'
        if psi_amount >= self.psi_alert or acc_drop >= self.acc_drop_pct:
            severity = 'high'
        elif psi_amount >= self.psi_warn or new_records >= self.min_new_records:
            severity = 'medium'
        elif days_since_train >= self.min_days_since_train:
            severity = 'low'
        
        # Make decision
        decision['needs_retrain'] = len(scope) > 0 and severity in ['medium', 'high']
        decision['reasons'] = reasons
        decision['scope'] = list(set(scope))
        decision['severity'] = severity
        
        logger.info(
            f"Drift decision: needs_retrain={decision['needs_retrain']}, "
            f"severity={severity}, reasons={len(reasons)}"
        )
        
        return decision
    
    def get_baseline_stats(self) -> Dict[str, Any]:
        """Get baseline statistics for comparison."""
        from app.db.models import ModelTrainingLogDB
        
        baseline_model = self.db.query(ModelTrainingLogDB).order_by(
            ModelTrainingLogDB.timestamp.desc()
        ).first()
        
        if not baseline_model:
            return {}
        
        return {
            'model_name': baseline_model.model_name,
            'accuracy': baseline_model.accuracy,
            'precision': baseline_model.precision_score,
            'recall': baseline_model.recall,
            'f1': baseline_model.f1_score,
            'records_used': baseline_model.records_used,
            'timestamp': baseline_model.timestamp.isoformat()
        }


def create_drift_monitor(db_session: Any, settings: Any) -> DriftMonitor:
    """
    Factory function to create drift monitor.
    
    Args:
        db_session: Database session
        settings: Settings object
        
    Returns:
        DriftMonitor instance
    """
    return DriftMonitor(db_session, settings)

