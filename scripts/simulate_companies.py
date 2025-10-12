#!/usr/bin/env python3
"""
Generate 5 simulated companies with realistic synthetic data for staging.

Creates:
- Company profiles with users
- Chart of accounts
- 12 months of bank transactions
- PDF receipts/invoices
- Vendor metadata

All data is synthetic and deterministic (seeded random).
"""
import sys
import json
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context, engine
from app.db.models import Base, UserDB, CompanyDB, UserCompanyLinkDB, TransactionDB
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Deterministic random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Company profiles
COMPANIES = [
    {
        "id": "hamilton_coffee",
        "name": "Hamilton Coffee Co.",
        "tax_id": "12-3456001",
        "business_type": "retail",
        "description": "Coffee shop with POS-heavy transactions",
        "monthly_revenue": (15000, 25000),
        "employee_name": "Sarah Hamilton",
        "email": "sarah@hamiltoncoffee.com"
    },
    {
        "id": "cincy_web",
        "name": "Cincy Web Builders LLC",
        "tax_id": "12-3456002",
        "business_type": "services",
        "description": "Web development contractor",
        "monthly_revenue": (30000, 50000),
        "employee_name": "Mike Chen",
        "email": "mike@cincyweb.com"
    },
    {
        "id": "liberty_childcare",
        "name": "Liberty Childcare Center",
        "tax_id": "12-3456003",
        "business_type": "childcare",
        "description": "Childcare with tuition and payroll",
        "monthly_revenue": (20000, 35000),
        "employee_name": "Jennifer Wilson",
        "email": "jen@libertychildcare.com"
    },
    {
        "id": "contreras_realestate",
        "name": "Contreras Real Estate Group",
        "tax_id": "12-3456004",
        "business_type": "realestate",
        "description": "Real estate with commissions and marketing",
        "monthly_revenue": (40000, 80000),
        "employee_name": "Carlos Contreras",
        "email": "carlos@contrerasrealty.com"
    },
    {
        "id": "midwest_accounting",
        "name": "Midwest Accounting Advisors",
        "tax_id": "12-3456005",
        "business_type": "professional_services",
        "description": "Accounting and advisory services",
        "monthly_revenue": (25000, 45000),
        "employee_name": "Lisa Thompson",
        "email": "lisa@midwestaccounting.com"
    }
]

# Vendor templates by business type
VENDORS = {
    "retail": {
        "suppliers": ["Coffee Bean Co", "Java Imports", "Roasters Supply", "Cafe Equipment LLC"],
        "utilities": ["Cincinnati Gas Electric", "Duke Energy", "AT&T"],
        "pos_systems": ["Square", "Clover", "Toast POS"],
        "misc": ["Amazon Business", "Costco", "Office Depot", "Uber Eats"],
    },
    "services": {
        "saas": ["AWS", "Digital Ocean", "GitHub", "Adobe Creative Cloud", "Figma"],
        "marketing": ["Google Ads", "Facebook Ads", "LinkedIn Sales Nav"],
        "tools": ["Slack", "Zoom", "Microsoft 365"],
        "misc": ["Amazon Business", "Staples", "FedEx"],
    },
    "childcare": {
        "supplies": ["School Specialty", "Lakeshore Learning", "Discount School Supply"],
        "food": ["Gordon Food Service", "Sysco", "Sam's Club"],
        "utilities": ["Cincinnati Water Works", "Duke Energy", "Spectrum"],
        "payroll": ["ADP", "Paychex"],
    },
    "realestate": {
        "marketing": ["Zillow Premier Agent", "Realtor.com", "Google Ads", "Facebook Ads"],
        "mls": ["MLS Cincinnati", "CoreLogic"],
        "tools": ["Dotloop", "DocuSign", "Matterport"],
        "misc": ["Office Depot", "FedEx", "Vistaprint"],
    },
    "professional_services": {
        "saas": ["QuickBooks", "Thomson Reuters", "CCH", "Practice CS"],
        "insurance": ["Professional Liability Ins", "Errors & Omissions"],
        "marketing": ["Google Ads", "LinkedIn", "Chamber of Commerce"],
        "misc": ["Office Depot", "FedEx", "Amazon Business"],
    }
}


def generate_chart_of_accounts(business_type: str) -> List[Dict[str, str]]:
    """Generate CoA tailored to business type."""
    base_coa = [
        {"account_num": "1000", "account_name": "Cash at Bank", "account_type": "BANK"},
        {"account_num": "1200", "account_name": "Accounts Receivable", "account_type": "AR"},
        {"account_num": "2000", "account_name": "Accounts Payable", "account_type": "AP"},
        {"account_num": "2100", "account_name": "Payroll Liabilities", "account_type": "OCLIAB"},
        {"account_num": "3000", "account_name": "Owner's Equity", "account_type": "EQUITY"},
        {"account_num": "8000", "account_name": "Sales Revenue", "account_type": "INC"},
        {"account_num": "6100", "account_name": "Office Supplies", "account_type": "EXP"},
        {"account_num": "6200", "account_name": "Utilities", "account_type": "EXP"},
        {"account_num": "6500", "account_name": "Travel & Transport", "account_type": "EXP"},
        {"account_num": "7000", "account_name": "Marketing & Advertising", "account_type": "EXP"},
    ]
    
    # Add business-specific accounts
    if business_type == "retail":
        base_coa.extend([
            {"account_num": "5000", "account_name": "Cost of Goods Sold", "account_type": "COGS"},
            {"account_num": "1400", "account_name": "Inventory", "account_type": "OASSET"},
            {"account_num": "6300", "account_name": "POS Fees", "account_type": "EXP"},
        ])
    elif business_type == "services":
        base_coa.extend([
            {"account_num": "6300", "account_name": "Software Subscriptions", "account_type": "EXP"},
            {"account_num": "6700", "account_name": "Contract Labor", "account_type": "EXP"},
        ])
    elif business_type == "childcare":
        base_coa.extend([
            {"account_num": "5100", "account_name": "Food & Supplies", "account_type": "COGS"},
            {"account_num": "6400", "account_name": "Payroll Expenses", "account_type": "EXP"},
            {"account_num": "8100", "account_name": "Tuition Revenue", "account_type": "INC"},
        ])
    elif business_type == "realestate":
        base_coa.extend([
            {"account_num": "8100", "account_name": "Commission Revenue", "account_type": "INC"},
            {"account_num": "6600", "account_name": "MLS Fees", "account_type": "EXP"},
        ])
    elif business_type == "professional_services":
        base_coa.extend([
            {"account_num": "8100", "account_name": "Consulting Revenue", "account_type": "INC"},
            {"account_num": "6800", "account_name": "Professional Insurance", "account_type": "EXP"},
        ])
    
    return base_coa


def generate_transactions(company: Dict, months: int = 12) -> List[Dict[str, Any]]:
    """Generate synthetic bank transactions for a company."""
    transactions = []
    vendors = VENDORS.get(company["business_type"], VENDORS["services"])
    
    start_date = datetime.now() - timedelta(days=365)
    
    for month in range(months):
        month_start = start_date + timedelta(days=30 * month)
        
        # Revenue (2-10 deposits per month)
        num_deposits = random.randint(2, 10)
        min_rev, max_rev = company["monthly_revenue"]
        
        for _ in range(num_deposits):
            date = month_start + timedelta(days=random.randint(1, 28))
            amount = round(random.uniform(min_rev / num_deposits * 0.5, max_rev / num_deposits * 1.5), 2)
            
            source = random.choice(["Square", "Stripe", "PayPal", "Wire Transfer", "Check"])
            
            transactions.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": amount,
                "description": f"{source} Payment",
                "counterparty": source,
                "currency": "USD"
            })
        
        # Expenses (15-30 per month)
        num_expenses = random.randint(15, 30)
        
        # Mix of recurring and one-time expenses
        all_vendors = []
        for category in vendors.values():
            all_vendors.extend(category)
        
        for _ in range(num_expenses):
            date = month_start + timedelta(days=random.randint(1, 28))
            vendor = random.choice(all_vendors)
            
            # Amount varies by vendor type
            if "Payroll" in vendor or "ADP" in vendor:
                amount = round(random.uniform(3000, 8000), 2)
            elif "Rent" in vendor or "Lease" in vendor:
                amount = round(random.uniform(2000, 5000), 2)
            elif "Ads" in vendor:
                amount = round(random.uniform(500, 2000), 2)
            else:
                amount = round(random.uniform(25, 500), 2)
            
            transactions.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": -amount,
                "description": f"{vendor} {'*' * 4}{random.randint(1000, 9999)}",
                "counterparty": vendor,
                "currency": "USD"
            })
    
    # Sort by date
    transactions.sort(key=lambda x: x["date"])
    
    return transactions


def save_transactions_csv(company_id: str, transactions: List[Dict], output_dir: Path):
    """Save transactions to CSV by month."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by month
    by_month = {}
    for txn in transactions:
        month_key = txn["date"][:7]  # YYYY-MM
        if month_key not in by_month:
            by_month[month_key] = []
        by_month[month_key].append(txn)
    
    # Save each month
    for month_key, month_txns in by_month.items():
        filename = output_dir / f"bank_{month_key.replace('-', '')}.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["date", "amount", "description", "counterparty", "currency"])
            writer.writeheader()
            writer.writerows(month_txns)
        
        logger.info(f"  Saved {len(month_txns)} transactions to {filename.name}")


def generate_pdf_stub(company_id: str, vendor: str, amount: float, date: str, output_path: Path):
    """Generate a stub PDF receipt (simplified - just creates placeholder)."""
    # In production, use ReportLab to generate actual PDFs
    # For now, create text file as placeholder
    content = f"""RECEIPT
Vendor: {vendor}
Date: {date}
Amount: ${amount:.2f}
Invoice #: {random.randint(10000, 99999)}

[Synthetic receipt for {company_id}]
"""
    
    with open(output_path, 'w') as f:
        f.write(content)


def generate_receipts(company_id: str, transactions: List[Dict], output_dir: Path, count: int = 100):
    """Generate PDF receipt stubs for random transactions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Select random expense transactions
    expenses = [t for t in transactions if t["amount"] < 0]
    selected = random.sample(expenses, min(count, len(expenses)))
    
    for i, txn in enumerate(selected):
        filename = output_dir / f"receipt_{i+1:03d}_{txn['date'].replace('-', '')}.txt"
        generate_pdf_stub(
            company_id,
            txn["counterparty"],
            abs(txn["amount"]),
            txn["date"],
            filename
        )
    
    logger.info(f"  Generated {len(selected)} receipt stubs")


def seed_companies():
    """Seed all simulated companies."""
    logger.info("=" * 70)
    logger.info("🏢 GENERATING SIMULATED COMPANIES")
    logger.info("=" * 70)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create output directories
    data_dir = Path(__file__).parent.parent / "data"
    csv_dir = data_dir / "simulated_csv"
    docs_dir = data_dir / "simulated_docs"
    metadata_dir = data_dir / "simulated_metadata"
    
    for dir_path in [csv_dir, docs_dir, metadata_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    with get_db_context() as db:
        for company in COMPANIES:
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 {company['name']} ({company['business_type']})")
            logger.info(f"{'='*70}")
            
            company_id = f"sim_{company['id']}"
            
            # Create user (simple hash for simulation)
            password_hash = hashlib.sha256("demo123".encode()).hexdigest()
            user = UserDB(
                user_id=f"user_{company['id']}",
                email=company['email'],
                hashed_password=password_hash,
                full_name=company['employee_name'],
                is_active=1
            )
            
            existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
            if not existing_user:
                db.add(user)
                db.flush()
                logger.info(f"  ✓ Created user: {user.email}")
            else:
                user = existing_user
                logger.info(f"  ℹ User exists: {user.email}")
            
            # Create company
            company_db = CompanyDB(
                company_id=company_id,
                company_name=company['name'],
                tax_id=company['tax_id'],
                currency="USD",
                is_active=1
            )
            
            existing_company = db.query(CompanyDB).filter(CompanyDB.company_id == company_id).first()
            if not existing_company:
                db.add(company_db)
                db.flush()
                logger.info(f"  ✓ Created company: {company['name']}")
            else:
                company_db = existing_company
                logger.info(f"  ℹ Company exists: {company['name']}")
            
            # Link user to company
            existing_link = db.query(UserCompanyLinkDB).filter(
                UserCompanyLinkDB.user_id == user.user_id,
                UserCompanyLinkDB.company_id == company_id
            ).first()
            
            if not existing_link:
                link = UserCompanyLinkDB(
                    user_id=user.user_id,
                    company_id=company_id,
                    role="owner"
                )
                db.add(link)
                logger.info(f"  ✓ Linked as owner")
            
            # Generate CoA
            logger.info(f"  📋 Generating chart of accounts...")
            coa = generate_chart_of_accounts(company['business_type'])
            coa_path = metadata_dir / company['id'] / "coa.json"
            coa_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(coa_path, 'w') as f:
                json.dump(coa, f, indent=2)
            logger.info(f"  ✓ Saved {len(coa)} accounts to {coa_path.name}")
            
            # Generate transactions
            logger.info(f"  💳 Generating 12 months of transactions...")
            transactions = generate_transactions(company, months=12)
            logger.info(f"  ✓ Generated {len(transactions)} transactions")
            
            # Save transactions by month
            logger.info(f"  💾 Saving transaction CSVs...")
            company_csv_dir = csv_dir / company['id']
            save_transactions_csv(company['id'], transactions, company_csv_dir)
            
            # Generate receipts
            logger.info(f"  📄 Generating receipt stubs...")
            company_docs_dir = docs_dir / company['id']
            num_receipts = random.randint(50, 200)
            generate_receipts(company['id'], transactions, company_docs_dir, count=num_receipts)
            
            # Save vendor metadata
            vendor_meta = {
                "business_type": company['business_type'],
                "vendors": VENDORS.get(company['business_type'], {}),
                "transaction_count": len(transactions),
                "receipt_count": num_receipts
            }
            vendor_path = metadata_dir / company['id'] / "vendors.json"
            with open(vendor_path, 'w') as f:
                json.dump(vendor_meta, f, indent=2)
            
            logger.info(f"  ✓ Saved vendor metadata")
        
        logger.info(f"\n{'='*70}")
        logger.info("✅ SIMULATION DATA GENERATION COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"\n📊 Summary:")
        logger.info(f"  Companies: {len(COMPANIES)}")
        logger.info(f"  Users: {len(COMPANIES)}")
        logger.info(f"  Data Directory: {data_dir}")
        logger.info(f"\n📁 Generated Files:")
        logger.info(f"  {csv_dir}")
        logger.info(f"  {docs_dir}")
        logger.info(f"  {metadata_dir}")


if __name__ == "__main__":
    try:
        seed_companies()
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

