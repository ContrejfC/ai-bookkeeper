#!/usr/bin/env python3
"""Seed script to load sample data into the database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import Base, TransactionDB, JournalEntryDB
from app.ingest.csv_parser import parse_csv_statement
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_sample_transactions():
    """Load sample transactions from CSV fixture."""
    # Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Tables created")
    
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_bank_statement.csv"
    
    if not fixture_path.exists():
        logger.error(f"Fixture file not found: {fixture_path}")
        return
    
    logger.info(f"Loading transactions from {fixture_path}")
    
    # Parse CSV
    transactions = parse_csv_statement(str(fixture_path))
    logger.info(f"Parsed {len(transactions)} transactions")
    
    # Save to database
    with get_db_context() as db:
        # Clear existing data
        db.query(JournalEntryDB).delete()
        db.query(TransactionDB).delete()
        
        for txn in transactions:
            db_txn = TransactionDB(
                txn_id=txn.txn_id,
                date=datetime.strptime(txn.date, "%Y-%m-%d").date(),
                amount=txn.amount,
                currency=txn.currency,
                description=txn.description,
                counterparty=txn.counterparty,
                raw=txn.raw,
                doc_ids=txn.doc_ids
            )
            db.add(db_txn)
        
        logger.info(f"Saved {len(transactions)} transactions to database")
    
    logger.info("✓ Sample data seeded successfully")


def seed_sample_rules():
    """Print info about sample rules."""
    rules_path = Path(__file__).parent.parent / "app" / "rules" / "vendor_rules.yaml"
    
    if rules_path.exists():
        logger.info(f"✓ Vendor rules file exists: {rules_path}")
    else:
        logger.warning(f"✗ Vendor rules file not found: {rules_path}")


if __name__ == "__main__":
    logger.info("Seeding sample data...")
    logger.info("=" * 60)
    
    seed_sample_transactions()
    seed_sample_rules()
    
    logger.info("=" * 60)
    logger.info("Done! You can now:")
    logger.info("  1. Start the API: uvicorn app.api.main:app --reload")
    logger.info("  2. Run propose: curl -X POST http://localhost:8000/api/post/propose")
    logger.info("  3. View review page: http://localhost:8000/ui/review")

