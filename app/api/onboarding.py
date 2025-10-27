"""
Onboarding API - New User Experience
====================================

This module provides endpoints for guided onboarding:
- Demo data generation
- Sample CSV download
- Initial setup help

Endpoints:
---------
- POST /api/onboarding/seed-demo - Create demo transactions
- GET /api/onboarding/sample-csv - Download sample CSV file
- GET /api/onboarding/status - Check onboarding progress
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import random

from app.db.session import get_db
from app.db.models import TransactionDB, CompanyDB
from app.auth.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Demo vendors and amounts
DEMO_VENDORS = [
    ("Amazon Web Services", 150.00, "Cloud hosting and services"),
    ("Google Workspace", 12.00, "G Suite subscription"),
    ("GitHub", 21.00, "Developer tools"),
    ("Stripe", 45.00, "Payment processing fees"),
    ("Microsoft Azure", 200.00, "Cloud infrastructure"),
    ("Zoom", 15.99, "Video conferencing"),
    ("Slack", 8.00, "Team communication"),
    ("Adobe Creative Cloud", 52.99, "Design software"),
    ("DigitalOcean", 60.00, "VPS hosting"),
    ("Twilio", 35.00, "SMS and voice services"),
]

DEMO_EXPENSE_CATEGORIES = [
    ("Office supplies", 50),
    ("Marketing", 200),
    ("Travel", 350),
    ("Meals & Entertainment", 75),
    ("Software licenses", 99),
    ("Professional services", 500),
    ("Equipment", 1200),
    ("Utilities", 150),
]


@router.post("/seed-demo")
async def seed_demo_data(
    tenant_id: str,
    count: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate demo transactions for onboarding.
    
    Creates realistic sample transactions with:
    - Common SaaS vendors
    - Various expense categories
    - Mixed income/expense
    - Dates over last 3 months
    
    Args:
        tenant_id: Tenant identifier
        count: Number of transactions to create (max 100)
        
    Returns:
        Summary of created transactions
    """
    # Validate count
    count = min(count, 100)
    
    # Check if tenant exists
    tenant_ids = current_user.tenant_ids if hasattr(current_user, 'tenant_ids') else []
    if tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="No access to this tenant")
    
    # Generate transactions
    transactions = []
    start_date = datetime.utcnow() - timedelta(days=90)
    
    logger.info(f"Generating {count} demo transactions for tenant {tenant_id}")
    
    for i in range(count):
        # Random date in last 90 days
        days_ago = random.randint(0, 90)
        txn_date = start_date + timedelta(days=days_ago)
        
        # Mix of vendors and expenses
        if i < len(DEMO_VENDORS) * 5:  # First ~50 are vendors
            vendor, base_amount, description = random.choice(DEMO_VENDORS)
            amount = -base_amount  # Expense (negative)
            counterparty = vendor
            desc = description
        else:  # Rest are varied expenses
            category, base_amount = random.choice(DEMO_EXPENSE_CATEGORIES)
            amount = -base_amount * random.uniform(0.5, 1.5)
            counterparty = f"{category} vendor"
            desc = f"{category} purchase"
        
        # Occasional income
        if random.random() < 0.1:  # 10% chance
            amount = abs(amount) * random.uniform(10, 50)
            counterparty = "Customer Inc"
            desc = "Invoice payment"
        
        txn = TransactionDB(
            txn_id=f"demo_{tenant_id}_{i}_{datetime.utcnow().timestamp()}",
            company_id=tenant_id,
            date=txn_date.date(),
            amount=round(amount, 2),
            currency="USD",
            description=desc,
            counterparty=counterparty,
            raw={"demo": True, "index": i}
        )
        
        db.add(txn)
        transactions.append(txn)
    
    db.commit()
    
    logger.info(f"Created {len(transactions)} demo transactions")
    
    return {
        "inserted": len(transactions),
        "tenant_id": tenant_id,
        "date_range": {
            "start": start_date.date().isoformat(),
            "end": datetime.utcnow().date().isoformat()
        }
    }


@router.get("/sample-csv")
async def get_sample_csv():
    """
    Download a sample bank statement CSV.
    
    Returns a packaged sample CSV file that users can use to test
    the import and categorization flow.
    
    Returns:
        CSV file download
    """
    # Path to sample CSV
    sample_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "fixtures",
        "sample_bank_statement.csv"
    )
    
    # Check if file exists
    if not os.path.exists(sample_path):
        # Generate one on the fly
        return generate_sample_csv_response()
    
    return FileResponse(
        sample_path,
        media_type="text/csv",
        filename="sample_bank_statement.csv"
    )


@router.get("/status")
async def get_onboarding_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get onboarding status for current user.
    
    Checks:
    - Has transactions uploaded
    - Has proposed journal entries
    - Has approved entries
    - Has connected accounting system
    
    Returns status and next steps.
    """
    # Get tenant_id
    tenant_ids = current_user.tenant_ids if hasattr(current_user, 'tenant_ids') else []
    if not tenant_ids:
        return {"status": "no_tenant", "next_step": "create_tenant"}
    
    tenant_id = tenant_ids[0]
    
    # Check progress
    from app.db.models import JournalEntryDB, QBOTokenDB
    
    has_transactions = db.query(TransactionDB).filter(
        TransactionDB.company_id == tenant_id
    ).count() > 0
    
    has_proposed = db.query(JournalEntryDB).filter(
        JournalEntryDB.status == 'proposed'
    ).count() > 0
    
    has_approved = db.query(JournalEntryDB).filter(
        JournalEntryDB.status == 'approved'
    ).count() > 0
    
    has_qbo = db.query(QBOTokenDB).filter(
        QBOTokenDB.tenant_id == tenant_id
    ).first() is not None
    
    # Determine next step
    if not has_transactions:
        next_step = "upload_transactions"
        progress = 0
    elif not has_proposed:
        next_step = "propose_entries"
        progress = 25
    elif not has_approved:
        next_step = "approve_entries"
        progress = 50
    elif not has_qbo:
        next_step = "connect_qbo"
        progress = 75
    else:
        next_step = "complete"
        progress = 100
    
    return {
        "status": "in_progress" if progress < 100 else "complete",
        "progress": progress,
        "next_step": next_step,
        "checks": {
            "has_transactions": has_transactions,
            "has_proposed": has_proposed,
            "has_approved": has_approved,
            "has_qbo": has_qbo
        }
    }


def generate_sample_csv_response():
    """Generate a sample CSV on the fly."""
    import tempfile
    import csv
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["Date", "Description", "Amount", "Currency", "Counterparty"])
        
        # Sample rows
        start_date = datetime.utcnow() - timedelta(days=30)
        
        for i, (vendor, amount, desc) in enumerate(DEMO_VENDORS):
            date = (start_date + timedelta(days=i*3)).strftime("%Y-%m-%d")
            writer.writerow([date, desc, f"-{amount}", "USD", vendor])
        
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        media_type="text/csv",
        filename="sample_bank_statement.csv"
    )
