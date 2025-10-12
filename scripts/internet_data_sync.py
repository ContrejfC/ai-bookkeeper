#!/usr/bin/env python3
"""
Internet Data Sync - Import open financial datasets.

Fetches, cleans, and imports financial data from open sources:
- Kaggle datasets (CSV)
- Sample financial datasets
- Mock data generators

Usage:
    python scripts/internet_data_sync.py --sources kaggle,sample
    python scripts/internet_data_sync.py --sources kaggle --limit 1000
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict, Any, Optional
import pandas as pd
import uuid

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import Base, TransactionDB, CompanyDB, OpenDataIngestionLogDB
from app.utils.open_data_cleaner import clean_open_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSource:
    """Base class for data sources."""
    
    def __init__(self, name: str):
        self.name = name
    
    def fetch(self) -> pd.DataFrame:
        """Fetch data from source."""
        raise NotImplementedError
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get source metadata."""
        return {
            'name': self.name,
            'type': 'unknown'
        }


class KaggleDataSource(DataSource):
    """Kaggle financial dataset source."""
    
    def __init__(self, dataset_path: str):
        super().__init__("kaggle")
        self.dataset_path = Path(dataset_path)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch from Kaggle dataset (CSV file)."""
        logger.info(f"Fetching Kaggle dataset from {self.dataset_path}")
        
        if not self.dataset_path.exists():
            logger.warning(f"Dataset not found: {self.dataset_path}")
            logger.info("Creating sample dataset for testing...")
            return self._create_sample_dataset()
        
        return pd.read_csv(self.dataset_path)
    
    def _create_sample_dataset(self) -> pd.DataFrame:
        """Create a sample dataset for testing."""
        import random
        from datetime import timedelta
        
        logger.info("Generating sample financial transactions...")
        
        vendors = [
            'Amazon Web Services', 'Microsoft Azure', 'Google Cloud',
            'Stripe Payment', 'Square Inc', 'PayPal Holdings',
            'Salesforce.com', 'Adobe Systems', 'Atlassian',
            'Office Depot', 'Staples Inc', 'FedEx',
            'American Express', 'Bank of America', 'Chase Bank',
            'Verizon', 'AT&T', 'Comcast',
            'Starbucks', 'Whole Foods', 'Target'
        ]
        
        records = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(1000):
            date = base_date + timedelta(days=random.randint(0, 365))
            vendor = random.choice(vendors)
            
            # Generate amount based on vendor type
            if 'Payment' in vendor or 'Square' in vendor or 'PayPal' in vendor:
                amount = round(random.uniform(500, 5000), 2)  # Revenue
            elif 'AWS' in vendor or 'Azure' in vendor or 'Cloud' in vendor:
                amount = -round(random.uniform(100, 1000), 2)  # Expense
            elif 'Office' in vendor or 'Staples' in vendor:
                amount = -round(random.uniform(50, 500), 2)
            else:
                amount = round(random.uniform(-500, 2000), 2)
            
            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'description': f"{vendor} Transaction {i}",
                'amount': amount,
                'counterparty': vendor,
                'currency': 'USD'
            })
        
        df = pd.DataFrame(records)
        logger.info(f"Generated {len(df)} sample transactions")
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': 'kaggle',
            'path': str(self.dataset_path)
        }


class SampleDataSource(DataSource):
    """Sample/demo data source."""
    
    def __init__(self, count: int = 500):
        super().__init__("sample")
        self.count = count
    
    def fetch(self) -> pd.DataFrame:
        """Generate sample financial data."""
        logger.info(f"Generating {self.count} sample transactions...")
        
        import random
        from datetime import timedelta
        
        transactions = []
        base_date = datetime(2023, 1, 1)
        
        # Vendor templates
        revenue_vendors = ['Stripe', 'Square', 'PayPal', 'Check Payment', 'Wire Transfer']
        expense_vendors = [
            'AWS', 'Google Ads', 'Microsoft 365', 'Slack', 'GitHub',
            'Office Depot', 'Staples', 'Amazon', 'FedEx', 'UPS',
            'Electric Company', 'Gas Utility', 'Water Utility',
            'Verizon', 'AT&T', 'Comcast'
        ]
        
        for i in range(self.count):
            date = base_date + timedelta(days=random.randint(0, 730))
            
            # 40% revenue, 60% expense
            if random.random() < 0.4:
                vendor = random.choice(revenue_vendors)
                amount = round(random.uniform(100, 5000), 2)
            else:
                vendor = random.choice(expense_vendors)
                amount = -round(random.uniform(50, 2000), 2)
            
            transactions.append({
                'date': date.strftime('%Y-%m-%d'),
                'description': f"{vendor} Transaction",
                'amount': amount,
                'counterparty': vendor,
                'currency': 'USD'
            })
        
        return pd.DataFrame(transactions)
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': 'sample',
            'count': self.count
        }


def get_data_source(source_type: str, **kwargs) -> DataSource:
    """
    Factory for data sources.
    
    Args:
        source_type: Type of source ('kaggle', 'sample', 'ofdp')
        **kwargs: Source-specific parameters
        
    Returns:
        DataSource instance
    """
    if source_type == 'kaggle':
        dataset_path = kwargs.get('dataset_path', 'data/kaggle/financial_transactions.csv')
        return KaggleDataSource(dataset_path)
    elif source_type == 'sample':
        count = kwargs.get('count', 500)
        return SampleDataSource(count)
    else:
        raise ValueError(f"Unknown source type: {source_type}")


def sync_data_source(
    source: DataSource,
    company_id: str = 'open_data_company',
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sync data from a source to database.
    
    Args:
        source: Data source to sync
        company_id: Company to assign transactions to
        limit: Maximum records to import
        
    Returns:
        Sync metrics dict
    """
    start_time = time.time()
    
    logger.info(f"="*70)
    logger.info(f"Syncing data from: {source.name}")
    logger.info(f"="*70)
    
    # Create ingestion log entry
    log_entry = {
        'source_name': source.name,
        'source_type': source.get_metadata().get('type'),
        'ingestion_metadata': source.get_metadata(),
        'status': 'pending',
        'timestamp': datetime.now()
    }
    
    try:
        # Fetch data
        logger.info("📥 Fetching data...")
        df = source.fetch()
        log_entry['record_count'] = len(df)
        
        if limit:
            df = df.head(limit)
            logger.info(f"   Limited to {limit} records")
        
        # Clean and normalize
        logger.info("🧹 Cleaning and normalizing...")
        df_clean = clean_open_dataset(df, source.name)
        
        # Ensure we have a company
        with get_db_context() as db:
            company = db.query(CompanyDB).filter(CompanyDB.company_id == company_id).first()
            if not company:
                logger.info(f"   Creating company: {company_id}")
                company = CompanyDB(
                    company_id=company_id,
                    company_name="Open Data Company",
                    currency="USD"
                )
                db.add(company)
                db.commit()
        
        # Import to database
        logger.info("💾 Importing to database...")
        imported_count = 0
        errors = 0
        error_details = []
        
        with get_db_context() as db:
            for idx, row in df_clean.iterrows():
                try:
                    # Generate unique transaction ID
                    txn_id = f"open_{source.name}_{uuid.uuid4().hex[:16]}"
                    
                    # Create transaction
                    txn = TransactionDB(
                        txn_id=txn_id,
                        company_id=company_id,
                        date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                        amount=float(row['amount']),
                        currency=row.get('currency', 'USD'),
                        description=row['description'],
                        counterparty=row.get('counterparty', ''),
                        raw={'original_row': idx},
                        source_type='open_data',
                        source_name=source.name
                    )
                    
                    db.add(txn)
                    imported_count += 1
                    
                    # Commit in batches of 100
                    if imported_count % 100 == 0:
                        db.commit()
                        logger.info(f"   Imported {imported_count} transactions...")
                
                except Exception as e:
                    errors += 1
                    error_details.append(f"Row {idx}: {str(e)}")
                    if errors <= 10:  # Only log first 10 errors
                        logger.error(f"   Error importing row {idx}: {e}")
            
            # Final commit
            db.commit()
        
        duration = time.time() - start_time
        
        # Update log entry
        log_entry.update({
            'records_imported': imported_count,
            'errors': errors,
            'error_details': error_details[:100],  # Limit error details
            'duration_seconds': duration,
            'status': 'success' if errors == 0 else 'partial_success'
        })
        
        # Save log to database
        with get_db_context() as db:
            log_db = OpenDataIngestionLogDB(**log_entry)
            db.add(log_db)
            db.commit()
        
        logger.info(f"\n✅ Sync complete!")
        logger.info(f"   Records: {imported_count}/{log_entry['record_count']}")
        logger.info(f"   Errors: {errors}")
        logger.info(f"   Duration: {duration:.2f}s")
        
        return {
            'success': True,
            'source': source.name,
            'imported': imported_count,
            'errors': errors,
            'duration': duration
        }
    
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(f"❌ Sync failed: {e}")
        
        log_entry.update({
            'records_imported': 0,
            'errors': 1,
            'error_details': [str(e)],
            'duration_seconds': duration,
            'status': 'failed'
        })
        
        # Save log
        with get_db_context() as db:
            log_db = OpenDataIngestionLogDB(**log_entry)
            db.add(log_db)
            db.commit()
        
        return {
            'success': False,
            'source': source.name,
            'error': str(e),
            'duration': duration
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Sync open financial datasets')
    parser.add_argument(
        '--sources',
        default='sample',
        help='Comma-separated list of sources (sample,kaggle)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit records per source'
    )
    parser.add_argument(
        '--company-id',
        default='open_data_company',
        help='Company ID to assign transactions to'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  INTERNET DATA SYNC - Open Dataset Integration")
    print("="*70 + "\n")
    
    # Ensure database tables exist
    logger.info("Ensuring database schema...")
    Base.metadata.create_all(bind=engine)
    
    # Parse sources
    sources_list = [s.strip() for s in args.sources.split(',')]
    
    results = []
    total_imported = 0
    total_errors = 0
    
    # Sync each source
    for source_type in sources_list:
        try:
            source = get_data_source(source_type, count=args.limit or 500)
            result = sync_data_source(source, company_id=args.company_id, limit=args.limit)
            results.append(result)
            
            if result['success']:
                total_imported += result['imported']
                total_errors += result['errors']
        
        except Exception as e:
            logger.error(f"Failed to process source {source_type}: {e}")
            results.append({
                'success': False,
                'source': source_type,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("  SYNC SUMMARY")
    print("="*70)
    print(f"\nSources processed: {len(results)}")
    print(f"Total imported: {total_imported}")
    print(f"Total errors: {total_errors}")
    print("\nDetails:")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['source']}: ", end='')
        if result['success']:
            print(f"{result['imported']} records ({result['duration']:.2f}s)")
        else:
            print(f"FAILED - {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*70)
    
    # Exit code
    sys.exit(0 if all(r['success'] for r in results) else 1)


if __name__ == "__main__":
    main()
