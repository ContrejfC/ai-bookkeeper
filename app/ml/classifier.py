"""ML classifier inference service."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import joblib
import scipy.sparse as sp
from datetime import datetime

logger = logging.getLogger(__name__)

# Global model cache
_model_cache = None


class MLClassifier:
    """ML-based transaction classifier."""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize classifier.
        
        Args:
            model_path: Path to trained model pickle file
        """
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent / "models" / "classifier.pkl"
        
        self.model_path = model_path
        self.artifacts = None
        self.is_loaded = False
        
        # Try to load model
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load model from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        global _model_cache
        
        # Check cache first
        if _model_cache is not None:
            self.artifacts = _model_cache
            self.is_loaded = True
            logger.info("Loaded model from cache")
            return True
        
        # Load from disk
        if not self.model_path.exists():
            logger.warning(f"Model not found at {self.model_path}")
            return False
        
        try:
            self.artifacts = joblib.load(self.model_path)
            _model_cache = self.artifacts  # Cache it
            self.is_loaded = True
            
            logger.info(f"Loaded {self.artifacts['model_type']} model")
            logger.info(f"  Trained: {self.artifacts['trained_at']}")
            logger.info(f"  Accuracy: {self.artifacts['test_accuracy']:.2%}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def _prepare_features(
        self,
        description: str,
        counterparty: str,
        amount: float,
        date: datetime
    ) -> sp.csr_matrix:
        """
        Prepare features for prediction.
        
        Args:
            description: Transaction description
            counterparty: Counterparty name
            amount: Transaction amount
            date: Transaction date
            
        Returns:
            Feature matrix
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        # Text features
        desc_features = self.artifacts['desc_vectorizer'].transform([description])
        counterparty_features = self.artifacts['counterparty_vectorizer'].transform([counterparty])
        
        # Numeric features
        amount_abs = abs(amount)
        is_positive = 1 if amount > 0 else 0
        
        # Amount bucket (hardcoded boundaries based on training)
        amount_bucket = min(int(np.log10(amount_abs + 1)), 9) if amount_abs > 0 else 0
        
        # Date features
        day_of_week = date.weekday()
        month = date.month
        
        numeric_features = np.array([[amount_abs, is_positive, amount_bucket, day_of_week, month]])
        
        # Combine
        X = sp.hstack([
            desc_features,
            counterparty_features,
            sp.csr_matrix(numeric_features)
        ])
        
        return X
    
    def predict_top_k(
        self,
        description: str,
        counterparty: str,
        amount: float,
        date: datetime,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Predict top-k accounts with probabilities.
        
        Args:
            description: Transaction description
            counterparty: Counterparty name
            amount: Transaction amount
            date: Transaction date
            k: Number of top predictions to return
            
        Returns:
            List of dicts with 'account', 'probability', 'rank'
        """
        if not self.is_loaded:
            logger.warning("Model not loaded, returning empty predictions")
            return []
        
        try:
            # Prepare features
            X = self._prepare_features(description, counterparty, amount, date)
            
            # Get predictions
            model = self.artifacts['model']
            model_type = self.artifacts['model_type']
            
            if model_type == 'lightgbm':
                probas = model.predict(X, num_iteration=model.best_iteration)
                # Reshape if needed
                if len(probas.shape) == 1:
                    probas = probas.reshape(1, -1)
            else:
                # Logistic Regression
                probas = model.predict_proba(X)
            
            # Get top-k
            top_k_idx = np.argsort(probas[0])[-k:][::-1]
            
            predictions = []
            for rank, idx in enumerate(top_k_idx, 1):
                account = self.artifacts['label_encoder'].classes_[idx]
                probability = float(probas[0][idx])
                
                predictions.append({
                    'account': account,
                    'probability': probability,
                    'rank': rank
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return []
    
    def predict(
        self,
        description: str,
        counterparty: str,
        amount: float,
        date: datetime
    ) -> Tuple[str, float]:
        """
        Predict single best account.
        
        Args:
            description: Transaction description
            counterparty: Counterparty name
            amount: Transaction amount
            date: Transaction date
            
        Returns:
            Tuple of (account, probability)
        """
        predictions = self.predict_top_k(description, counterparty, amount, date, k=1)
        
        if predictions:
            return predictions[0]['account'], predictions[0]['probability']
        else:
            return "Unknown", 0.0


# Singleton instance
_classifier_instance = None


def get_classifier() -> MLClassifier:
    """Get or create classifier instance."""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = MLClassifier()
    
    return _classifier_instance

