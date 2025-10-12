#!/usr/bin/env python3
"""
Train ML classifier for transaction categorization.

Reads training data from data/feedback/training.csv and trains a LightGBM model.
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import joblib
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Feature engineering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)

# Try LightGBM, fall back to LogisticRegression
try:
    import lightgbm as lgb
    USE_LIGHTGBM = True
    print("✅ Using LightGBM")
except (ImportError, OSError):
    # OSError catches system dependency issues (e.g., libomp on macOS)
    from sklearn.linear_model import LogisticRegression
    USE_LIGHTGBM = False
    print("⚠️  LightGBM not available, using LogisticRegression")


def load_training_data(data_path: Path) -> pd.DataFrame:
    """Load and validate training data."""
    print(f"\n📂 Loading training data from {data_path}...")
    
    df = pd.read_csv(data_path)
    
    print(f"   Loaded {len(df):,} records")
    print(f"   Columns: {', '.join(df.columns)}")
    print(f"   Companies: {df['company_id'].nunique()}")
    print(f"   Unique accounts: {df['approved_account'].nunique()}")
    
    return df


def engineer_features(df: pd.DataFrame):
    """
    Create features for the model.
    
    Features:
    - TF-IDF of description (top 500 terms)
    - TF-IDF of counterparty (top 100 terms)
    - Amount bucket (10 bins)
    - Day of week
    - Month
    - Is positive/negative amount
    """
    print("\n🔧 Engineering features...")
    
    # Text features for description
    desc_vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        min_df=2,
        strip_accents='unicode'
    )
    desc_features = desc_vectorizer.fit_transform(df['description'].fillna(''))
    
    # Text features for counterparty
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
    
    # Combine all features
    import scipy.sparse as sp
    
    numeric_features = df[['amount_abs', 'is_positive', 'amount_bucket', 'day_of_week', 'month']].values
    
    X = sp.hstack([
        desc_features,
        counterparty_features,
        sp.csr_matrix(numeric_features)
    ])
    
    print(f"   Feature matrix shape: {X.shape}")
    print(f"   Description vocab: {len(desc_vectorizer.vocabulary_)}")
    print(f"   Counterparty vocab: {len(counterparty_vectorizer.vocabulary_)}")
    
    return X, desc_vectorizer, counterparty_vectorizer


def train_model(X, y, test_size=0.2, random_state=42):
    """Train the classification model."""
    print("\n🤖 Training model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"   Training set: {X_train.shape[0]:,} samples")
    print(f"   Test set: {X_test.shape[0]:,} samples")
    
    if USE_LIGHTGBM:
        # LightGBM
        params = {
            'objective': 'multiclass',
            'num_class': len(np.unique(y)),
            'metric': 'multi_logloss',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'n_jobs': -1
        }
        
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=10)]
        )
    else:
        # Logistic Regression fallback
        model = LogisticRegression(
            max_iter=1000,
            multi_class='ovr',  # One-vs-rest for better performance on small datasets
            solver='liblinear',  # Better for small datasets
            random_state=random_state,
            C=1.0
        )
        model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = model.predict(X_train) if USE_LIGHTGBM else model.predict(X_train)
    y_pred_test = model.predict(X_test) if USE_LIGHTGBM else model.predict(X_test)
    
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    
    print(f"\n📊 Model Performance:")
    print(f"   Training accuracy: {train_acc:.2%}")
    print(f"   Test accuracy: {test_acc:.2%}")
    
    return model, X_test, y_test, y_pred_test


def generate_report(
    model,
    y_test,
    y_pred_test,
    label_encoder,
    output_path: Path
):
    """Generate model metrics report."""
    print("\n📝 Generating report...")
    
    # Calculate metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred_test, average='weighted'
    )
    
    # Per-class metrics
    class_report = classification_report(
        y_test, y_pred_test,
        target_names=label_encoder.classes_,
        output_dict=True
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred_test)
    
    # Write markdown report
    with open(output_path, 'w') as f:
        f.write("# ML Classifier v1 - Model Metrics Report\n\n")
        f.write(f"**Training Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Type:** {'LightGBM' if USE_LIGHTGBM else 'LogisticRegression'}\n")
        f.write(f"**Test Set Size:** {len(y_test):,} samples\n\n")
        
        f.write("## Overall Metrics\n\n")
        f.write(f"- **Accuracy:** {accuracy_score(y_test, y_pred_test):.2%}\n")
        f.write(f"- **Precision (weighted):** {precision:.2%}\n")
        f.write(f"- **Recall (weighted):** {recall:.2%}\n")
        f.write(f"- **F1 Score (weighted):** {f1:.2%}\n\n")
        
        f.write("## Per-Class Performance\n\n")
        f.write("| Account | Precision | Recall | F1-Score | Support |\n")
        f.write("|---------|-----------|--------|----------|----------|\n")
        
        for account in label_encoder.classes_:
            if account in class_report:
                metrics = class_report[account]
                f.write(f"| {account} | {metrics['precision']:.2%} | {metrics['recall']:.2%} | {metrics['f1-score']:.2%} | {int(metrics['support'])} |\n")
        
        f.write("\n## Top Performing Classes (by F1-Score)\n\n")
        
        # Sort by F1-score
        class_scores = []
        for account in label_encoder.classes_:
            if account in class_report:
                class_scores.append((account, class_report[account]['f1-score']))
        
        class_scores.sort(key=lambda x: x[1], reverse=True)
        
        f.write("| Rank | Account | F1-Score |\n")
        f.write("|------|---------|----------|\n")
        
        for idx, (account, score) in enumerate(class_scores[:10], 1):
            f.write(f"| {idx} | {account} | {score:.2%} |\n")
        
        f.write("\n## Confusion Matrix\n\n")
        f.write("*(Top 5 most common classes)*\n\n")
        
        # Show top 5 classes by support
        top_classes = sorted(class_report.items(), key=lambda x: x[1].get('support', 0) if isinstance(x[1], dict) else 0, reverse=True)[:5]
        top_class_names = [c[0] for c in top_classes if isinstance(c[1], dict)]
        
        f.write("| Predicted → | " + " | ".join([name.split()[-2] for name in top_class_names]) + " |\n")
        f.write("|------------|" + "|".join(["-------" for _ in top_class_names]) + "|\n")
        
        for name in top_class_names:
            try:
                row_str = name.split()[-2] if len(name.split()) >= 2 else name[:10]
                f.write(f"| {row_str} | ")
                
                # Get indices for this class
                idx = list(label_encoder.classes_).index(name)
                row_values = []
                for other_name in top_class_names:
                    other_idx = list(label_encoder.classes_).index(other_name)
                    row_values.append(str(cm[idx][other_idx]))
                
                f.write(" | ".join(row_values) + " |\n")
            except (ValueError, IndexError):
                continue  # Skip invalid entries like 'macro avg'
        
        f.write("\n## Feature Importance\n\n")
        f.write("*(Feature importance only available for tree-based models)*\n\n")
        
        if USE_LIGHTGBM:
            importance = model.feature_importance()
            top_features_idx = np.argsort(importance)[-10:][::-1]
            
            f.write("| Rank | Feature Index | Importance |\n")
            f.write("|------|---------------|------------|\n")
            
            for rank, idx in enumerate(top_features_idx, 1):
                f.write(f"| {rank} | {idx} | {importance[idx]:.1f} |\n")
        else:
            f.write("*Not applicable for LogisticRegression*\n")
        
        f.write("\n## Recommendations\n\n")
        
        test_acc = accuracy_score(y_test, y_pred_test)
        
        if test_acc >= 0.80:
            f.write("- ✅ **Model meets 80% accuracy target**\n")
            f.write("- Ready for production deployment\n")
            f.write("- Consider A/B testing against current system\n")
        else:
            f.write(f"- ⚠️ **Model accuracy ({test_acc:.2%}) below 80% target**\n")
            f.write("- Collect more training data\n")
            f.write("- Add more features (vendor embeddings, transaction amount patterns)\n")
            f.write("- Try ensemble methods\n")
        
        f.write("\n## Next Steps\n\n")
        f.write("1. Deploy model to staging\n")
        f.write("2. Run live evaluation on simulated tenants\n")
        f.write("3. Monitor auto-approval rate\n")
        f.write("4. Retrain monthly with new feedback data\n")
    
    print(f"   Report saved to: {output_path}")


def main():
    """Main training pipeline."""
    print("\n" + "="*70)
    print("  ML CLASSIFIER TRAINING PIPELINE v1")
    print("="*70)
    
    # Paths
    data_path = Path(__file__).parent.parent / "data" / "feedback" / "training.csv"
    model_dir = Path(__file__).parent.parent / "models"
    reports_dir = Path(__file__).parent.parent / "reports"
    
    model_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    
    # Load data
    df = load_training_data(data_path)
    
    # Prepare target
    print("\n🎯 Preparing target variable...")
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df['approved_account'])
    print(f"   Number of classes: {len(label_encoder.classes_)}")
    
    # Engineer features
    X, desc_vectorizer, counterparty_vectorizer = engineer_features(df)
    
    # Train model
    model, X_test, y_test, y_pred_test = train_model(X, y)
    
    # Generate report
    report_path = reports_dir / "model_metrics.md"
    generate_report(model, y_test, y_pred_test, label_encoder, report_path)
    
    # Save model and artifacts
    model_path = model_dir / "classifier.pkl"
    artifacts = {
        'model': model,
        'label_encoder': label_encoder,
        'desc_vectorizer': desc_vectorizer,
        'counterparty_vectorizer': counterparty_vectorizer,
        'model_type': 'lightgbm' if USE_LIGHTGBM else 'logistic_regression',
        'trained_at': datetime.now().isoformat(),
        'test_accuracy': float(accuracy_score(y_test, y_pred_test))
    }
    
    joblib.dump(artifacts, model_path)
    print(f"\n💾 Model saved to: {model_path}")
    
    # Save metadata
    metadata = {
        'model_type': artifacts['model_type'],
        'trained_at': artifacts['trained_at'],
        'test_accuracy': artifacts['test_accuracy'],
        'num_classes': len(label_encoder.classes_),
        'training_samples': len(df),
        'feature_dimensions': X.shape[1]
    }
    
    metadata_path = model_dir / "classifier_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"📄 Metadata saved to: {metadata_path}")
    
    print("\n✅ Training complete!")
    print(f"   Test Accuracy: {artifacts['test_accuracy']:.2%}")
    print(f"   Model ready for deployment")
    
    return artifacts['test_accuracy']


if __name__ == "__main__":
    accuracy = main()
    
    if accuracy >= 0.80:
        print("\n🎉 SUCCESS: Model achieves ≥80% accuracy target!")
        sys.exit(0)
    else:
        print(f"\n⚠️  WARNING: Model accuracy ({accuracy:.2%}) below 80% target")
        print("   Consider collecting more training data or improving features")
        sys.exit(1)

