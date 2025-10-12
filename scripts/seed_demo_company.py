#!/usr/bin/env python3
"""Seed script to create a demo company with sample data for beta testing."""
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import (
    Base, UserDB, CompanyDB, UserCompanyLinkDB,
    TransactionDB, JournalEntryDB
)
from app.ingest.csv_parser import parse_csv_statement
from app.auth.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_demo_company():
    """Create a complete demo company with sample data."""
    logger.info("=" * 70)
    logger.info("🎭 SEEDING DEMO COMPANY")
    logger.info("=" * 70)
    
    # Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Tables created")
    
    with get_db_context() as db:
        # Create demo user
        logger.info("\n👤 Creating demo user...")
        demo_user = UserDB(
            user_id="user_demo_001",
            email="demo@aibookkeeper.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            is_active=1,
            is_superuser=0
        )
        
        # Check if exists
        existing = db.query(UserDB).filter(UserDB.email == demo_user.email).first()
        if existing:
            logger.info(f"  User already exists: {existing.email}")
            demo_user = existing
        else:
            db.add(demo_user)
            db.flush()
            logger.info(f"  ✓ Created user: {demo_user.email}")
            logger.info(f"    User ID: {demo_user.user_id}")
            logger.info(f"    Password: demo123")
        
        # Create demo company
        logger.info("\n🏢 Creating demo company...")
        demo_company = CompanyDB(
            company_id="company_demo_001",
            company_name="Demo Company LLC",
            tax_id="12-3456789",
            currency="USD",
            fiscal_year_end="12-31",
            is_active=1
        )
        
        existing = db.query(CompanyDB).filter(CompanyDB.company_id == demo_company.company_id).first()
        if existing:
            logger.info(f"  Company already exists: {existing.company_name}")
            demo_company = existing
        else:
            db.add(demo_company)
            db.flush()
            logger.info(f"  ✓ Created company: {demo_company.company_name}")
            logger.info(f"    Company ID: {demo_company.company_id}")
        
        # Link user to company
        logger.info("\n🔗 Linking user to company...")
        existing_link = db.query(UserCompanyLinkDB).filter(
            UserCompanyLinkDB.user_id == demo_user.user_id,
            UserCompanyLinkDB.company_id == demo_company.company_id
        ).first()
        
        if not existing_link:
            link = UserCompanyLinkDB(
                user_id=demo_user.user_id,
                company_id=demo_company.company_id,
                role="owner"
            )
            db.add(link)
            logger.info(f"  ✓ Linked {demo_user.email} to {demo_company.company_name} as owner")
        else:
            logger.info(f"  Link already exists")
        
        # Load sample transactions
        logger.info("\n📄 Loading sample transactions...")
        fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_bank_statement.csv"
        
        if not fixture_path.exists():
            logger.error(f"  ✗ Fixture file not found: {fixture_path}")
            return
        
        # Clear existing demo data
        db.query(JournalEntryDB).filter(
            JournalEntryDB.company_id == demo_company.company_id
        ).delete()
        db.query(TransactionDB).filter(
            TransactionDB.company_id == demo_company.company_id
        ).delete()
        db.flush()
        
        # Parse and load transactions
        transactions = parse_csv_statement(str(fixture_path))
        logger.info(f"  Parsed {len(transactions)} transactions from CSV")
        
        for txn in transactions:
            db_txn = TransactionDB(
                txn_id=txn.txn_id,
                company_id=demo_company.company_id,  # Link to demo company
                date=datetime.strptime(txn.date, "%Y-%m-%d").date(),
                amount=txn.amount,
                currency=txn.currency,
                description=txn.description,
                counterparty=txn.counterparty,
                raw=txn.raw,
                doc_ids=txn.doc_ids
            )
            db.add(db_txn)
        
        db.flush()
        logger.info(f"  ✓ Loaded {len(transactions)} transactions")
        
        # Generate sample journal entries (simplified)
        logger.info("\n📝 Generating sample journal entries...")
        je_count = 0
        
        for txn in db.query(TransactionDB).filter(
            TransactionDB.company_id == demo_company.company_id
        ).limit(10).all():
            # Create a simple balanced entry
            amount = abs(txn.amount)
            
            if txn.amount > 0:
                # Revenue
                lines = [
                    {"account": "1000 Cash at Bank", "debit": amount, "credit": 0.0},
                    {"account": "8000 Sales Revenue", "debit": 0.0, "credit": amount}
                ]
            else:
                # Expense
                lines = [
                    {"account": "6100 Office Supplies", "debit": amount, "credit": 0.0},
                    {"account": "1000 Cash at Bank", "debit": 0.0, "credit": amount}
                ]
            
            je = JournalEntryDB(
                je_id=f"je_{uuid.uuid4().hex[:16]}",
                company_id=demo_company.company_id,
                date=txn.date,
                lines=lines,
                source_txn_id=txn.txn_id,
                memo="Demo journal entry",
                confidence=0.95,
                status="proposed",
                needs_review=0
            )
            db.add(je)
            je_count += 1
        
        db.flush()
        logger.info(f"  ✓ Created {je_count} sample journal entries")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ DEMO COMPANY SEEDED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info("\n📋 Demo Account Details:")
        logger.info(f"  Email: {demo_user.email}")
        logger.info(f"  Password: demo123")
        logger.info(f"  Company ID: {demo_company.company_id}")
        logger.info(f"  Company Name: {demo_company.company_name}")
        logger.info(f"  Transactions: {len(transactions)}")
        logger.info(f"  Journal Entries: {je_count}")
        logger.info("\n🚀 Next Steps:")
        logger.info("  1. Start the server: uvicorn app.api.main:app --reload")
        logger.info("  2. Login:")
        logger.info("     curl -X POST http://localhost:8000/api/auth/login \\")
        logger.info("       -d 'username=demo@aibookkeeper.com&password=demo123'")
        logger.info("  3. View dashboard: http://localhost:8000/ui/dashboard")
        logger.info("  4. Run propose: curl -X POST http://localhost:8000/api/post/propose")
        logger.info("")


if __name__ == "__main__":
    try:
        seed_demo_company()
    except Exception as e:
        logger.error(f"\n❌ Error seeding demo company: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

