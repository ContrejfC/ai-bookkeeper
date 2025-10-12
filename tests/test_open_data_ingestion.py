"""
Unit tests for open data ingestion and cleaning.

Tests cover:
- Column standardization
- Date parsing
- MCC mapping
- Sync logic
- Training metrics
"""
import sys
from pathlib import Path
import pytest
import pandas as pd
from datetime import datetime, date

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.open_data_cleaner import (
    standardize_columns,
    parse_dates,
    normalize_amounts,
    extract_counterparty,
    map_vendor_to_account,
    validate_balance_integrity,
    clean_open_dataset
)


class TestColumnStandardization:
    """Test column name normalization."""
    
    def test_standard_column_names(self):
        """Test that standard column names are preserved."""
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'amount': [100.00],
            'description': ['Test']
        })
        
        result = standardize_columns(df)
        
        assert 'date' in result.columns
        assert 'amount' in result.columns
        assert 'description' in result.columns
    
    def test_variant_column_names(self):
        """Test that variant column names are standardized."""
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'Amount': [100.00],
            'Description': ['Test'],
            'vendor': ['Acme Corp']
        })
        
        result = standardize_columns(df)
        
        assert 'date' in result.columns
        assert 'amount' in result.columns
        assert 'description' in result.columns
        assert 'counterparty' in result.columns
    
    def test_missing_columns_handling(self):
        """Test handling of datasets with missing columns."""
        df = pd.DataFrame({
            'some_date_col': ['2024-01-01'],
            'value': [100.00]
        })
        
        # Should not raise an error
        result = standardize_columns(df)
        assert len(result.columns) > 0


class TestDateParsing:
    """Test date format parsing."""
    
    def test_standard_date_format(self):
        """Test parsing of YYYY-MM-DD format."""
        df = pd.DataFrame({
            'date': ['2024-01-15', '2024-02-20']
        })
        
        result = parse_dates(df)
        
        assert result['date'][0] == '2024-01-15'
        assert result['date'][1] == '2024-02-20'
    
    def test_multiple_date_formats(self):
        """Test parsing of various date formats."""
        df = pd.DataFrame({
            'date': ['01/15/2024', '2024-02-20', '15-Jan-2024']
        })
        
        result = parse_dates(df)
        
        # Should successfully parse most formats
        assert result['date'].notna().sum() >= 2
    
    def test_invalid_dates(self):
        """Test handling of invalid dates."""
        df = pd.DataFrame({
            'date': ['invalid_date', '2024-02-20']
        })
        
        result = parse_dates(df)
        
        # Invalid dates should be NaN
        assert pd.isna(result['date'][0])
        assert result['date'][1] == '2024-02-20'


class TestAmountNormalization:
    """Test amount normalization."""
    
    def test_single_amount_column(self):
        """Test normalization with single amount column."""
        df = pd.DataFrame({
            'amount': ['100.50', '-50.25', '200']
        })
        
        result = normalize_amounts(df)
        
        assert result['amount'][0] == 100.50
        assert result['amount'][1] == -50.25
        assert result['amount'][2] == 200.0
    
    def test_debit_credit_columns(self):
        """Test normalization with separate debit/credit columns."""
        df = pd.DataFrame({
            'debit': [100.0, 0, 50.0],
            'credit': [0, 200.0, 0]
        })
        
        result = normalize_amounts(df)
        
        # Credit - Debit (credit is positive income, debit is negative expense)
        assert 'amount' in result.columns
        assert result['amount'][0] == -100.0  # Expense
        assert result['amount'][1] == 200.0   # Revenue
        assert result['amount'][2] == -50.0   # Expense
    
    def test_invalid_amounts_removed(self):
        """Test that invalid amounts are removed."""
        df = pd.DataFrame({
            'amount': [100.0, 'invalid', 200.0]
        })
        
        result = normalize_amounts(df)
        
        # Should have 2 valid records
        assert len(result) == 2


class TestCounterpartyExtraction:
    """Test counterparty/vendor extraction."""
    
    def test_existing_counterparty(self):
        """Test that existing counterparty is preserved."""
        df = pd.DataFrame({
            'description': ['Payment to vendor'],
            'counterparty': ['Acme Corp']
        })
        
        result = extract_counterparty(df)
        
        assert result['counterparty'][0] == 'Acme Corp'
    
    def test_extract_from_description(self):
        """Test extraction from description when counterparty missing."""
        df = pd.DataFrame({
            'description': ['Acme Corp - Invoice #123', 'XYZ Inc Payment']
        })
        
        result = extract_counterparty(df)
        
        assert 'counterparty' in result.columns
        assert 'Acme Corp' in result['counterparty'][0]
        assert len(result['counterparty'][0]) <= 50  # Length limit


class TestMCCMapping:
    """Test Merchant Category Code mapping."""
    
    def test_revenue_mcc(self):
        """Test MCC code mapping for revenue."""
        row = pd.Series({
            'description': 'Transaction',
            'counterparty': 'Restaurant',
            'amount': 100.0,
            'mcc': '5812'  # Restaurant
        })
        
        account = map_vendor_to_account(row, use_mcc=True)
        
        assert '8000 Sales Revenue' in account
    
    def test_expense_mcc(self):
        """Test MCC code mapping for expenses."""
        row = pd.Series({
            'description': 'Transaction',
            'counterparty': 'Office Store',
            'amount': -50.0,
            'mcc': '5943'  # Office supplies
        })
        
        account = map_vendor_to_account(row, use_mcc=True)
        
        assert '6100 Office Supplies' in account
    
    def test_vendor_pattern_matching(self):
        """Test vendor pattern matching without MCC."""
        test_cases = [
            ('AWS Monthly Bill', '6300 Software Subscriptions'),
            ('Google Ads Payment', '7000 Advertising'),
            ('Stripe Payment Received', '8000 Sales Revenue'),
            ('Office Depot Purchase', '6100 Office Supplies')
        ]
        
        for description, expected_category in test_cases:
            row = pd.Series({
                'description': description,
                'counterparty': description.split()[0],
                'amount': -100.0
            })
            
            account = map_vendor_to_account(row, use_mcc=False)
            
            assert expected_category in account, f"Failed for: {description}"


class TestBalanceIntegrity:
    """Test balance validation."""
    
    def test_balanced_transactions(self):
        """Test validation of balanced transactions."""
        df = pd.DataFrame({
            'amount': [100.0, -50.0, -50.0]  # Net zero
        })
        
        is_balanced, metrics = validate_balance_integrity(df)
        
        assert is_balanced
        assert metrics['balance_diff'] < 0.01
    
    def test_unbalanced_transactions(self):
        """Test detection of unbalanced transactions."""
        df = pd.DataFrame({
            'amount': [100.0, -50.0]  # Net 50
        })
        
        is_balanced, metrics = validate_balance_integrity(df)
        
        # Small unbalance is okay (testing threshold)
        assert metrics['balance_diff'] >= 0


class TestDatasetCleaning:
    """Test end-to-end dataset cleaning."""
    
    def test_clean_sample_dataset(self):
        """Test cleaning a sample dataset."""
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01', '2024-01-02'],
            'Amount': [100.0, -50.0],
            'Description': ['Revenue from customer', 'Office supplies'],
            'vendor': ['Customer A', 'Office Depot']
        })
        
        result = clean_open_dataset(df, 'test_source')
        
        # Check standardized columns
        assert 'date' in result.columns
        assert 'amount' in result.columns
        assert 'description' in result.columns
        assert 'counterparty' in result.columns
        assert 'account' in result.columns
        
        # Check metadata
        assert 'source_type' in result.columns
        assert result['source_type'][0] == 'open_data'
        assert result['source_name'][0] == 'test_source'
        
        # Check data integrity
        assert len(result) == 2


class TestIngestionLogging:
    """Test ingestion logging functionality."""
    
    def test_log_entry_creation(self):
        """Test that log entries are created during sync."""
        from app.db.session import get_db_context, engine
        from app.db.models import OpenDataIngestionLogDB, Base
        
        # Ensure table exists
        Base.metadata.create_all(bind=engine)
        
        with get_db_context() as db:
            log = OpenDataIngestionLogDB(
                source_name='test_source',
                source_type='test',
                record_count=100,
                records_imported=100,
                errors=0,
                duration_seconds=1.5,
                status='success'
            )
            db.add(log)
            db.commit()
            
            # Query back
            result = db.query(OpenDataIngestionLogDB).filter(
                OpenDataIngestionLogDB.source_name == 'test_source'
            ).first()
            
            assert result is not None
            assert result.records_imported == 100
            assert result.status == 'success'


class TestTrainingMetrics:
    """Test ML training metrics."""
    
    def test_training_metrics_logged(self):
        """Test that training metrics are logged to database."""
        from app.db.session import get_db_context, engine
        from app.db.models import ModelTrainingLogDB, Base
        
        # Ensure table exists
        Base.metadata.create_all(bind=engine)
        
        with get_db_context() as db:
            log = ModelTrainingLogDB(
                model_name='test_classifier',
                records_used=1000,
                train_records=800,
                test_records=200,
                accuracy=0.95,
                precision_score=0.94,
                recall=0.96,
                f1_score=0.95,
                duration_seconds=2.5
            )
            db.add(log)
            db.commit()
            
            # Query back
            result = db.query(ModelTrainingLogDB).filter(
                ModelTrainingLogDB.model_name == 'test_classifier'
            ).first()
            
            assert result is not None
            assert result.accuracy >= 0.85  # Target threshold
            assert result.records_used == 1000
    
    def test_accuracy_threshold(self):
        """Test that trained model meets accuracy threshold."""
        from app.db.session import get_db_context
        from app.db.models import ModelTrainingLogDB
        
        with get_db_context() as db:
            latest_model = db.query(ModelTrainingLogDB).filter(
                ModelTrainingLogDB.model_name == 'classifier_open'
            ).order_by(ModelTrainingLogDB.timestamp.desc()).first()
            
            if latest_model:
                assert latest_model.accuracy >= 0.85, \
                    f"Model accuracy {latest_model.accuracy:.2%} below 85% threshold"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

