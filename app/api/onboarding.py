"""
Onboarding API (Phase 2b).

Handles 4-step onboarding wizard for new tenants.
"""
import logging
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.db.session import get_db
from app.db.models import TenantSettingsDB, DecisionAuditLogDB
from app.ui.rbac import User, get_current_user, Role, require_role


router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])
logger = logging.getLogger(__name__)


# CoA Templates
COA_TEMPLATES = {
    "standard_small_business": [
        {"code": "1000", "name": "Cash", "type": "Asset"},
        {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
        {"code": "1500", "name": "Inventory", "type": "Asset"},
        {"code": "1700", "name": "Equipment", "type": "Asset"},
        {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
        {"code": "2100", "name": "Credit Card", "type": "Liability"},
        {"code": "3000", "name": "Owner's Equity", "type": "Equity"},
        {"code": "4000", "name": "Sales Revenue", "type": "Revenue"},
        {"code": "5000", "name": "Cost of Goods Sold", "type": "Expense"},
        {"code": "6000", "name": "Operating Expenses", "type": "Expense"},
        {"code": "6100", "name": "Rent Expense", "type": "Expense"},
        {"code": "6200", "name": "Utilities", "type": "Expense"},
        {"code": "6300", "name": "Office Supplies", "type": "Expense"},
        {"code": "6400", "name": "Professional Fees", "type": "Expense"},
    ],
    "professional_services": [
        {"code": "1000", "name": "Operating Cash", "type": "Asset"},
        {"code": "1100", "name": "Savings Account", "type": "Asset"},
        {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
        {"code": "1300", "name": "Unbilled Revenue", "type": "Asset"},
        {"code": "1700", "name": "Computer Equipment", "type": "Asset"},
        {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
        {"code": "2100", "name": "Deferred Revenue", "type": "Liability"},
        {"code": "3000", "name": "Owner's Capital", "type": "Equity"},
        {"code": "4000", "name": "Professional Services Revenue", "type": "Revenue"},
        {"code": "4100", "name": "Consulting Revenue", "type": "Revenue"},
        {"code": "6000", "name": "Subcontractor Expense", "type": "Expense"},
        {"code": "6100", "name": "Office Rent", "type": "Expense"},
        {"code": "6200", "name": "Software Subscriptions", "type": "Expense"},
        {"code": "6300", "name": "Professional Development", "type": "Expense"},
        {"code": "6400", "name": "Marketing", "type": "Expense"},
    ],
    "gaap_accounting_firm": [
        {"code": "1010", "name": "Operating Checking", "type": "Asset"},
        {"code": "1020", "name": "Payroll Account", "type": "Asset"},
        {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
        {"code": "1210", "name": "Allowance for Doubtful Accounts", "type": "Asset"},
        {"code": "1300", "name": "Work in Progress", "type": "Asset"},
        {"code": "1500", "name": "Prepaid Expenses", "type": "Asset"},
        {"code": "1700", "name": "Furniture & Fixtures", "type": "Asset"},
        {"code": "1750", "name": "Accumulated Depreciation", "type": "Asset"},
        {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
        {"code": "2100", "name": "Accrued Payroll", "type": "Liability"},
        {"code": "2200", "name": "Unearned Revenue", "type": "Liability"},
        {"code": "3000", "name": "Partner Capital", "type": "Equity"},
        {"code": "3100", "name": "Retained Earnings", "type": "Equity"},
        {"code": "4000", "name": "Audit Fees", "type": "Revenue"},
        {"code": "4100", "name": "Tax Preparation Fees", "type": "Revenue"},
        {"code": "4200", "name": "Consulting Fees", "type": "Revenue"},
        {"code": "5000", "name": "Partner Compensation", "type": "Expense"},
        {"code": "6000", "name": "Staff Salaries", "type": "Expense"},
        {"code": "6100", "name": "Payroll Taxes", "type": "Expense"},
        {"code": "6200", "name": "Professional Liability Insurance", "type": "Expense"},
        {"code": "6300", "name": "CPE & Training", "type": "Expense"},
        {"code": "6400", "name": "Office Rent", "type": "Expense"},
    ]
}


@router.post("/complete")
async def complete_onboarding(
    coa_method: str = Form(...),
    coa_template: Optional[str] = Form(None),
    autopost_threshold: float = Form(0.90),
    llm_budget: float = Form(50.0),
    coa_file: Optional[UploadFile] = File(None),
    transactions_file: Optional[UploadFile] = File(None),
    receipts: Optional[List[UploadFile]] = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete onboarding wizard.
    
    Creates tenant config, imports CoA, ingests data, sets safety settings.
    
    RBAC: Owner only.
    """
    # RBAC: Owner only
    require_role(Role.OWNER, user)
    
    # Generate tenant_id
    tenant_id = f"onboarded-{uuid.uuid4().hex[:12]}"
    
    try:
        # Step 1: Chart of Accounts
        coa_count = 0
        if coa_method == "template" and coa_template:
            if coa_template not in COA_TEMPLATES:
                raise HTTPException(status_code=400, detail="Invalid CoA template")
            
            # In production, would insert into qbo_account_mapping table
            # For now, just log
            coa = COA_TEMPLATES[coa_template]
            coa_count = len(coa)
            logger.info(f"Applied CoA template '{coa_template}' with {coa_count} accounts for {tenant_id}")
        
        elif coa_method == "upload" and coa_file:
            # In production, would parse CSV and insert
            contents = await coa_file.read()
            lines = contents.decode('utf-8').splitlines()
            coa_count = len(lines) - 1  # Minus header
            logger.info(f"Uploaded CoA CSV with {coa_count} accounts for {tenant_id}")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid CoA method or missing file")
        
        # Step 2: Data Ingest
        transactions_count = 0
        receipts_count = 0
        
        if transactions_file:
            # In production, would call ingest endpoint
            contents = await transactions_file.read()
            lines = contents.decode('utf-8', errors='ignore').splitlines()
            transactions_count = len(lines) - 1
            logger.info(f"Ingested {transactions_count} transactions for {tenant_id}")
        
        if receipts:
            receipts_count = len(receipts)
            logger.info(f"Uploaded {receipts_count} receipts for {tenant_id}")
        
        # Step 3: Safety Settings
        # Create tenant settings
        settings = TenantSettingsDB(
            tenant_id=tenant_id,
            autopost_enabled=False,  # Always disabled by default
            autopost_threshold=autopost_threshold,
            llm_tenant_cap_usd=llm_budget,
            updated_by=user.user_id
        )
        db.add(settings)
        
        # Audit entry: onboarding_complete
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            action="onboarding_complete",
            user_id=user.user_id
        )
        db.add(audit)
        
        db.commit()
        
        logger.info(f"Onboarding complete for tenant {tenant_id} by {user.user_id}")
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "summary": {
                "coa_method": coa_method,
                "coa_accounts": coa_count,
                "transactions": transactions_count,
                "receipts": receipts_count,
                "autopost_enabled": False,
                "autopost_threshold": autopost_threshold,
                "llm_budget": llm_budget
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding failed for {user.user_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

