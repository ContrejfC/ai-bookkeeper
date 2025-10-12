#!/usr/bin/env python3
"""
Train ML classifier from merged dataset (simulated + open data).

This script loads all transactions from the database, generates features,
trains a classifier, and saves the model with metrics.

Usage:
    python scripts/train_from_open_data.py
    python scripts/train_from_open_data.py --save_model true
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import time
import json
import joblib
import numpy as np
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import Base, TransactionDB, JournalEntryDB, ModelTrainingLogDB
from app.utils.open_data_cleaner import map_vendor_to_account

# ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_training_data() -> pd.DataFrame:
    """
    Load all transactions with associated accounts from database.
    
    Returns:
        DataFrame with transaction data
    """
    logger.info("Loading training data from database...")
    
    with get_db_context() as db:
        # Join transactions with journal entries to get actual accounts
        query = db.query(
            TransactionDB.txn_id,
            TransactionDB.company_id,
            TransactionDB.date,
            TransactionDB.amount,
            TransactionDB.description,
            TransactionDB.counterparty,
            TransactionDB.source_type,
            TransactionDB.source_name,
            JournalEntryDB.lines
        ).outerjoin(
            JournalEntryDB,
            TransactionDB.txn_id == JournalEntryDB.source_txn_id
        )
        
        results = query.all()
        
        records = []
        for row in results:
            # Extract account from JE lines
            account = None
            if row.lines:
                for line in row.lines:
                    if 'Cash at Bank' not in line.get('account', ''):
                        account = line.get('account')
                        break
            
            # If no JE, map from vendor/description
            if not account:
                account = map_vendor_to_account(pd.Series({
                    'description': row.description or '',
                    'counterparty': row.counterparty or '',
                    'amount': row.amount
                }))
            
            records.append({
                'txn_id': row.txn_id,
                'company_id': row.company_id,
                'date': row.date,
                'amount': row.amount,
                'description': row.description or '',
                'counterparty': row.counterparty or '',
                'source_type': row.source_type or 'unknown',
                'source_name': row.source_name or 'unknown',
                'account': account
            })
    
    df = pd.DataFrame(records)
    
    logger.info(f"   Loaded {len(df)} transactions")
    logger.info(f"   Source breakdown:")
    for source_type, count in df['source_type'].value_counts().items():
        logger.info(f"      {source_type}: {count}")
    logger.info(f"   Unique accounts: {df['account'].nunique()}")
    
    return df


def engineer_features(df: pd.DataFrame):
    """
    Generate ML features from transaction data.
    
    Args:
        df: DataFrame with transactions
        
    Returns:
        Tuple of (X, y, vectorizers, label_encoder)
    """
    logger.info("Engineering features...")
    
    # Text vectorization
    desc_vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        min_df=2,
        strip_accents='unicode'
    )
    desc_features = desc_vectorizer.fit_transform(df['description'].fillna(''))
    
    counterparty_vectorizer = TfidfVectorizer(
        max_features=100,
        min_df=2,
        strip_accents='unicode'
    )
    counterparty_features = counterparty_vectorizer.fit_transform(df['counterparty'].fillna(''))
    
    # Numeric features
    df['amount_abs'] = df['amount'].abs()
    df['is_positive'] = (df['amount'] > 0).astype(int)
    df['amount_bucket'] = pd.qcut(df['amount_abs'], q=10, labels=False, duplicates='drop')
    
    # Date features
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    
    # Combine features
    import scipy.sparse as sp
    
    numeric_features = df[['amount_abs', 'is_positive', 'amount_bucket', 'day_of_week', 'month']].values
    
    X = sp.hstack([
        desc_features,
        counterparty_features,
        sp.csr_matrix(numeric_features)
    ])
    
    # Target encoding
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df['account'])
    
    logger.info(f"   Feature matrix: {X.shape}")
    logger.info(f"   Vocabulary size: {len(desc_vectorizer.vocabulary_) + len(counterparty_vectorizer.vocabulary_)}")
    logger.info(f"   Classes: {len(label_encoder.classes_)}")
    
    artifacts = {
        'desc_vectorizer': desc_vectorizer,
        'counterparty_vectorizer': counterparty_vectorizer,
        'label_encoder': label_encoder
    }
    
    return X, y, artifacts


def train_model(X, y, test_size=0.2, random_state=42):
    """
    Train logistic regression classifier.
    
    Args:
        X: Feature matrix
        y: Target labels
        test_size: Fraction for test set
        random_state: Random seed
        
    Returns:
        Tuple of (model, X_test, y_test, y_pred_test, metrics)
    """
    logger.info("Training model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"   Training: {X_train.shape[0]} samples")
    logger.info(f"   Test: {X_test.shape[0]} samples")
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        multi_class='ovr',
        solver='liblinear',
        random_state=random_state,
        C=1.0
    )
    
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Metrics
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred_test, average='weighted', zero_division=0
    )
    
    logger.info(f"\n   Training accuracy: {train_acc:.2%}")
    logger.info(f"   Test accuracy: {test_acc:.2%}")
    logger.info(f"   Precision: {precision:.2%}")
    logger.info(f"   Recall: {recall:.2%}")
    logger.info(f"   F1 Score: {f1:.2%}")
    
    metrics = {
        'train_accuracy': float(train_acc),
        'test_accuracy': float(test_acc),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'train_samples': int(X_train.shape[0]),
        'test_samples': int(X_test.shape[0])
    }
    
    return model, X_test, y_test, y_pred_test, metrics


def save_model(model, artifacts, metrics, output_dir: Path):
    """
    Save trained model and artifacts.
    
    Args:
        model: Trained classifier
        artifacts: Dict with vectorizers and encoders
        metrics: Training metrics
        output_dir: Directory to save to
    """
    logger.info("Saving model...")
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Save model bundle
    model_bundle = {
        'model': model,
        'label_encoder': artifacts['label_encoder'],
        'desc_vectorizer': artifacts['desc_vectorizer'],
        'counterparty_vectorizer': artifacts['counterparty_vectorizer'],
        'model_type': 'logistic_regression',
        'trained_at': datetime.now().isoformat(),
        'metrics': metrics
    }
    
    model_path = output_dir / "classifier_open.pkl"
    joblib.dump(model_bundle, model_path)
    
    logger.info(f"   Model saved to: {model_path}")
    
    # Save metadata
    metadata = {
        'model_name': 'classifier_open',
        'model_type': 'LogisticRegression',
        'trained_at': model_bundle['trained_at'],
        **metrics
    }
    
    metadata_path = output_dir / "classifier_open_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"   Metadata saved to: {metadata_path}")


def log_training_metrics(metrics: dict, records_used: int):
    """
    Save training metrics to database.
    
    Args:
        metrics: Training metrics dict
        records_used: Number of records used
    """
    logger.info("Logging metrics to database...")
    
    with get_db_context() as db:
        log_entry = ModelTrainingLogDB(
            model_name='classifier_open',
            records_used=records_used,
            train_records=metrics['train_samples'],
            test_records=metrics['test_samples'],
            accuracy=metrics['test_accuracy'],
            precision_score=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            duration_seconds=metrics.get('duration', 0),
            model_metadata={'model_type': 'LogisticRegression'},
            timestamp=datetime.now()
        )
        db.add(log_entry)
        db.commit()
    
    logger.info("   Metrics logged successfully")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train classifier on merged dataset')
    parser.add_argument(
        '--save_model',
        default='true',
        help='Whether to save the model (true/false)'
    )
    parser.add_argument(
        '--output_dir',
        default='models',
        help='Directory to save model'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  ML TRAINING PIPELINE - Merged Dataset")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Load data
    df = load_training_data()
    
    if len(df) == 0:
        logger.error("No training data found!")
        return 1
    
    # Engineer features
    X, y, artifacts = engineer_features(df)
    
    # Train model
    model, X_test, y_test, y_pred_test, metrics = train_model(X, y)
    
    duration = time.time() - start_time
    metrics['duration'] = duration
    
    # Save model
    if args.save_model.lower() == 'true':
        output_dir = Path(args.output_dir)
        save_model(model, artifacts, metrics, output_dir)
        log_training_metrics(metrics, len(df))
    
    # Summary
    print("\n" + "="*70)
    print("  TRAINING COMPLETE")
    print("="*70)
    print(f"\nDataset: {len(df)} transactions")
    print(f"Training: {metrics['train_samples']} samples")
    print(f"Test: {metrics['test_samples']} samples")
    print(f"\nPerformance:")
    print(f"  Accuracy:  {metrics['test_accuracy']:.2%}")
    print(f"  Precision: {metrics['precision']:.2%}")
    print(f"  Recall:    {metrics['recall']:.2%}")
    print(f"  F1 Score:  {metrics['f1_score']:.2%}")
    print(f"\nDuration: {duration:.2f}s")
    
    if metrics['test_accuracy'] >= 0.85:
        print("\n✅ SUCCESS: Model achieves ≥85% accuracy target!")
        return 0
    else:
        print(f"\n⚠️  WARNING: Model accuracy ({metrics['test_accuracy']:.2%}) below 85% target")
        return 1


if __name__ == "__main__":
    sys.exit(main())

