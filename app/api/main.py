"""FastAPI application main entry point."""
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from app.db.session import get_db, engine
from app.db.models import (
    Base, Transaction, JournalEntry, JournalEntryLine,
    TransactionDB, JournalEntryDB, ReconciliationDB
)
from app.ingest.csv_parser import parse_csv_statement
from app.rules.engine import RulesEngine
from app.vendor_knowledge.embeddings import vendor_kb
from app.llm.categorize_post import llm_categorizer
from app.recon.matcher import ReconciliationMatcher
from app.exporters.csv_export import (
    export_journal_entries_csv,
    export_reconciliation_csv,
    export_general_ledger_csv,
    export_trial_balance_csv
)
from app.exporters.quickbooks_export import QuickBooksExporter, XeroExporter
from app.importers.quickbooks_import import QuickBooksImporter, XeroImporter
from app.api import auth as auth_router
from app.api.financial_reports.pnl import generate_pnl
from app.api.financial_reports.balance_sheet import generate_balance_sheet
from app.api.financial_reports.cashflow import generate_cashflow
from app.api.financial_reports.automation_metrics import get_automation_metrics, get_automation_trend
from app.auth.security import get_company_id_from_token, require_role
from config.settings import settings
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Bookkeeper",
    description="AI-powered bookkeeping with automated journal entry posting",
    version="0.2.1-beta"
)

# ============================================================================
# P1.1 Security Patch: CSRF Protection Middleware
# ============================================================================
from app.auth.csrf import csrf_protect

# Add CSRF middleware
app.middleware("http")(csrf_protect)
logger.info("✅ CSRF protection middleware enabled")

# ============================================================================
# Wave-2 Phase 1, 2a & 2b: Import and register API routes
# ============================================================================
try:
    from app.api import tenants, auth as wave2_auth, rules, audit_export, billing, notifications, onboarding, receipts, analytics as analytics_api
    from app.ui import routes as ui_routes
    
    # Include Phase 1 routers
    app.include_router(wave2_auth.router)
    app.include_router(tenants.router)
    app.include_router(rules.router)
    app.include_router(audit_export.router)
    
    # Include Phase 2a routers
    app.include_router(billing.router)
    app.include_router(notifications.router)
    
    # Include Phase 2b routers
    app.include_router(onboarding.router)
    app.include_router(receipts.router)
    app.include_router(analytics_api.router)
    
    # Include UI routes
    app.include_router(ui_routes.router, tags=["ui"])
    
    # Mount static files for UI
    try:
        app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
    except:
        pass  # Static directory may not exist in all environments
    
    logger.info("✅ Wave-2 Phase 1, 2a & 2b routes loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  Wave-2 routes not available: {e}")


@app.get("/healthz")
async def health_check(db: Session = Depends(get_db)):
    """
    Lightweight health check for monitoring and load balancers (Sprint 9 Stage B).
    
    Quick snapshot without writes. For comprehensive checks with writes, use /readyz.
    
    Returns:
        JSON with uptime, versions, db ping, and component status
    """
    import subprocess
    import time
    from sqlalchemy import text
    
    start_time = time.time()
    
    # Get git SHA if available
    git_sha = "unknown"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=Path(__file__).parent.parent.parent
        )
        if result.returncode == 0:
            git_sha = result.stdout.strip()
    except Exception:
        pass
    
    # Database ping (no writes, just SELECT 1)
    db_ping_start = time.time()
    db_status = "healthy"
    db_ping_ms = 0.0
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        db_ping_ms = round((time.time() - db_ping_start) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        db_ping_ms = -1.0
    
    # Get ruleset version (from rules engine or latest rule_versions)
    ruleset_version_id = "unknown"
    try:
        from app.rules.engine import RulesEngine
        rules_engine = RulesEngine()
        ruleset_version_id = getattr(rules_engine, 'current_version', 'v0.0.1')
    except Exception:
        ruleset_version_id = "v0.0.1"  # Default fallback
    
    # Get model version (from ML classifier metadata)
    model_version_id = "unknown"
    try:
        from pathlib import Path
        import json
        metadata_path = Path(settings.MODEL_REGISTRY) / "classifier_open_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                model_version_id = metadata.get("version", "m1.0.0")
        else:
            model_version_id = "m1.0.0"  # Default if no metadata
    except Exception:
        model_version_id = "m1.0.0"
    
    # OCR stub status
    ocr_stub_loaded = False
    try:
        from app.ocr import parser as ocr_parser
        ocr_stub_loaded = True
    except ImportError:
        ocr_stub_loaded = False
    
    # Vector store status
    vector_store_status = settings.vector_backend or "none"
    
    # Calculate uptime (mock for now - would track app start time in production)
    uptime_seconds = round(time.time() - start_time + 300, 1)  # Mock: +300s for demo
    
    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "uptime_seconds": uptime_seconds,
        "version": "0.2.0-beta",
        "git_sha": git_sha,
        "ruleset_version_id": ruleset_version_id,
        "model_version_id": model_version_id,
        "db_ping_ms": db_ping_ms,
        "database_status": db_status,
        "ocr_stub_loaded": ocr_stub_loaded,
        "vector_store_status": vector_store_status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/readyz")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint for Kubernetes/load balancers (Sprint 9 Stage A).
    
    Verifies:
    - Database connectivity
    - Schema migrations at head
    - Write/read smoke test
    - OCR stub availability
    - Vector store status
    
    Returns:
        JSON with detailed component status and timings
    """
    import subprocess
    import time
    from sqlalchemy import text, inspect
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.migration import MigrationContext
    
    start_time = time.time()
    checks = {}
    overall_ready = True
    
    # 1. Database Connectivity Check
    db_start = time.time()
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database_connect"] = {
            "status": "ok",
            "timing_ms": round((time.time() - db_start) * 1000, 2)
        }
    except Exception as e:
        checks["database_connect"] = {
            "status": "error",
            "error": str(e),
            "timing_ms": round((time.time() - db_start) * 1000, 2)
        }
        overall_ready = False
    
    # 2. Migrations at Head Check
    migration_start = time.time()
    try:
        # Get current revision from database
        context = MigrationContext.configure(db.connection())
        current_rev = context.get_current_revision()
        
        # Get head revision from alembic scripts
        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script_dir.get_current_head()
        
        if current_rev == head_rev:
            checks["migrations"] = {
                "status": "ok",
                "current": current_rev or "None",
                "head": head_rev,
                "timing_ms": round((time.time() - migration_start) * 1000, 2)
            }
        else:
            checks["migrations"] = {
                "status": "warning",
                "current": current_rev or "None",
                "head": head_rev,
                "message": "Migrations not at head",
                "timing_ms": round((time.time() - migration_start) * 1000, 2)
            }
            overall_ready = False
    except Exception as e:
        checks["migrations"] = {
            "status": "error",
            "error": str(e),
            "timing_ms": round((time.time() - migration_start) * 1000, 2)
        }
        overall_ready = False
    
    # 3. Write/Read Smoke Test
    smoke_start = time.time()
    try:
        # Create temp table, insert, select, drop
        test_id = str(uuid.uuid4())[:8]
        table_name = f"readyz_test_{test_id}"
        
        # Create temp table
        db.execute(text(f"CREATE TEMP TABLE {table_name} (id INTEGER, value TEXT)"))
        
        # Insert
        db.execute(text(f"INSERT INTO {table_name} (id, value) VALUES (1, 'test')"))
        
        # Select
        result = db.execute(text(f"SELECT value FROM {table_name} WHERE id = 1"))
        row = result.fetchone()
        
        # Drop
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        if row and row[0] == "test":
            checks["write_read_smoke"] = {
                "status": "ok",
                "timing_ms": round((time.time() - smoke_start) * 1000, 2)
            }
        else:
            checks["write_read_smoke"] = {
                "status": "error",
                "error": "Write/read mismatch",
                "timing_ms": round((time.time() - smoke_start) * 1000, 2)
            }
            overall_ready = False
    except Exception as e:
        checks["write_read_smoke"] = {
            "status": "error",
            "error": str(e),
            "timing_ms": round((time.time() - smoke_start) * 1000, 2)
        }
        overall_ready = False
    
    # 4. OCR Stub Availability
    ocr_start = time.time()
    try:
        # Check if OCR module is importable
        from app.ocr import parser as ocr_parser
        checks["ocr_stub"] = {
            "status": "ok",
            "available": True,
            "timing_ms": round((time.time() - ocr_start) * 1000, 2)
        }
    except ImportError:
        checks["ocr_stub"] = {
            "status": "warning",
            "available": False,
            "message": "OCR module not found (expected for Stage A)",
            "timing_ms": round((time.time() - ocr_start) * 1000, 2)
        }
        # Not a blocker for Stage A
    
    # 5. Vector Store Status
    vector_start = time.time()
    try:
        vector_status = settings.vector_backend
        checks["vector_store"] = {
            "status": "ok",
            "backend": vector_status,
            "message": "Vector store disabled (as expected)" if vector_status == "none" else f"Using {vector_status}",
            "timing_ms": round((time.time() - vector_start) * 1000, 2)
        }
    except Exception as e:
        checks["vector_store"] = {
            "status": "error",
            "error": str(e),
            "timing_ms": round((time.time() - vector_start) * 1000, 2)
        }
        overall_ready = False
    
    total_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "ready": overall_ready,
        "checks": checks,
        "total_timing_ms": total_time,
        "timestamp": datetime.now().isoformat()
    }

# Include routers
app.include_router(auth_router.router)

# Setup templates and static files
templates = Jinja2Templates(directory="app/ui/templates")
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")


# ============================================================================
# Job Status API (Async Queue)
# ============================================================================

@app.get("/api/jobs/{job_id}")
async def get_job_status_api(job_id: str):
    """
    Get status of a background job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status with progress and result
    """
    try:
        from app.worker.queue import get_job_status
        status = get_job_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/company/{company_id}")
async def get_company_jobs_api(company_id: str, limit: int = 50):
    """
    Get recent jobs for a company.
    
    Args:
        company_id: Company identifier
        limit: Maximum jobs to return
        
    Returns:
        List of job statuses
    """
    try:
        from app.worker.queue import get_company_jobs
        jobs = get_company_jobs(company_id, limit)
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create tables
Base.metadata.create_all(bind=engine)

# Chart of Accounts (hardcoded for MVP)
CHART_OF_ACCOUNTS = [
    "1000 Cash at Bank",
    "2000 Credit Card Payable",
    "2100 Taxes Payable",
    "5000 Cost of Goods Sold",
    "6100 Office Supplies",
    "6150 Computer Equipment",
    "6200 Utilities",
    "6300 Software Subscriptions",
    "6400 Entertainment",
    "6500 Travel & Transport",
    "6600 Shipping & Freight",
    "6700 Contract Labor",
    "6800 Insurance",
    "6900 Rent Expense",
    "6950 Bank Fees",
    "6999 Miscellaneous Expense",
    "7000 Advertising",
    "8000 Sales Revenue",
    "8100 Payroll Income",
]

# Initialize rules engine
rules_engine = RulesEngine()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Bookkeeper API",
        "version": "0.1.0",
        "endpoints": {
            "upload": "/api/upload",
            "propose": "/api/post/propose",
            "approve": "/api/post/approve",
            "reconcile": "/api/reconcile/run",
            "review": "/ui/review"
        }
    }


@app.post("/api/upload")
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a bank statement (CSV/OFX/PDF).
    
    Returns the parsed transactions.
    """
    # Save uploaded file temporarily
    temp_path = f"/tmp/{uuid.uuid4().hex}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Parse based on file extension
        if file.filename.endswith('.csv'):
            transactions = parse_csv_statement(temp_path)
        elif file.filename.endswith('.ofx'):
            from app.ingest.ofx_parser import parse_ofx_statement
            transactions = parse_ofx_statement(temp_path)
        elif file.filename.endswith('.pdf'):
            from app.ingest.pdf_bank_parser import parse_pdf_statement
            transactions = parse_pdf_statement(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Save transactions to database
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
            db.merge(db_txn)
        
        db.commit()
        
        return {
            "message": f"Uploaded and parsed {len(transactions)} transactions",
            "transactions": [txn.model_dump() for txn in transactions]
        }
    
    finally:
        # Cleanup temp file
        Path(temp_path).unlink(missing_ok=True)


@app.post("/api/post/propose")
async def propose_journal_entries(
    txn_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Generate proposed journal entries for transactions.
    
    Uses tiered decisioning: rules → embeddings → LLM → human review
    """
    # Get transactions to process
    if txn_ids:
        db_txns = db.query(TransactionDB).filter(TransactionDB.txn_id.in_(txn_ids)).all()
    else:
        # Get all unprocessed transactions (no JE yet)
        db_txns = db.query(TransactionDB).filter(
            ~TransactionDB.txn_id.in_(
                db.query(JournalEntryDB.source_txn_id).filter(JournalEntryDB.source_txn_id.isnot(None))
            )
        ).all()
    
    if not db_txns:
        return {"message": "No transactions to process", "proposed": []}
    
    proposed_jes = []
    
    for db_txn in db_txns:
        # Convert to Pydantic model
        txn = Transaction(
            txn_id=db_txn.txn_id,
            date=db_txn.date.strftime("%Y-%m-%d"),
            amount=db_txn.amount,
            currency=db_txn.currency,
            description=db_txn.description,
            counterparty=db_txn.counterparty,
            raw=db_txn.raw,
            doc_ids=db_txn.doc_ids or []
        )
        
        logger.info(f"Processing transaction: {txn.txn_id} - {txn.description}")
        
        # Tier 1: Rules engine
        rule_match = rules_engine.match_transaction(txn)
        
        if rule_match and rule_match.get('matched') and rule_match.get('confidence', 0) >= 0.9:
            # High confidence rule match
            logger.info(f"  ✓ Matched by rule: {rule_match['account']}")
            llm_result = _create_simple_je_from_rule(txn, rule_match)
        else:
            # Tier 2: Check embeddings memory
            similar = vendor_kb.find_similar(
                txn.counterparty or "",
                txn.description,
                n_results=3
            )
            
            historical_mappings = []
            if similar:
                logger.info(f"  ✓ Found {len(similar)} similar transactions")
                historical_mappings = similar
            
            # Tier 3: LLM
            logger.info(f"  → Using LLM categorization")
            llm_result = llm_categorizer.categorize_transaction(
                txn,
                CHART_OF_ACCOUNTS,
                historical_mappings
            )
        
        # Create JournalEntry
        je = llm_categorizer.create_journal_entry(txn, llm_result)
        
        # Tier 4: Force human review if needed
        if abs(txn.amount) > settings.large_amount_threshold:
            je.needs_review = True
            je.memo = f"LARGE AMOUNT (>${settings.large_amount_threshold}). " + (je.memo or "")
        
        # Save to database
        db_je = JournalEntryDB(
            je_id=je.je_id,
            date=datetime.strptime(je.date, "%Y-%m-%d").date(),
            lines=[line.model_dump() for line in je.lines],
            source_txn_id=je.source_txn_id,
            memo=je.memo,
            confidence=je.confidence,
            status=je.status,
            needs_review=1 if je.needs_review else 0
        )
        db.add(db_je)
        
        proposed_jes.append(je.model_dump())
    
    db.commit()
    
    return {
        "message": f"Proposed {len(proposed_jes)} journal entries",
        "proposed": proposed_jes,
        "review_needed": sum(1 for je in proposed_jes if je.get('needs_review'))
    }


def _create_simple_je_from_rule(txn: Transaction, rule_match: dict) -> dict:
    """Create a simple journal entry from rule match."""
    amount = abs(txn.amount)
    account = rule_match['account']
    
    if txn.amount > 0:
        # Revenue
        lines = [
            {"account": "1000 Cash at Bank", "debit": amount, "credit": 0.0},
            {"account": account, "debit": 0.0, "credit": amount}
        ]
    else:
        # Expense
        lines = [
            {"account": account, "debit": amount, "credit": 0.0},
            {"account": "1000 Cash at Bank", "debit": 0.0, "credit": amount}
        ]
    
    return {
        "account": account,
        "journal_entry": {
            "date": txn.date,
            "lines": lines
        },
        "confidence": rule_match.get('confidence', 1.0),
        "needs_review": False,
        "rationale": rule_match.get('rationale', 'Matched by rules engine')
    }


@app.post("/api/post/approve")
async def approve_journal_entries(
    je_ids: List[str],
    action: str = "approve",  # approve or post
    db: Session = Depends(get_db)
):
    """
    Approve or post journal entries.
    
    - approve: Mark as approved
    - post: Mark as posted and add to vendor knowledge
    """
    if action not in ["approve", "post"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'post'")
    
    jes = db.query(JournalEntryDB).filter(JournalEntryDB.je_id.in_(je_ids)).all()
    
    if not jes:
        raise HTTPException(status_code=404, detail="No journal entries found")
    
    updated = []
    
    for je in jes:
        # Check if balanced before posting
        lines = je.lines
        total_debits = sum(line['debit'] for line in lines)
        total_credits = sum(line['credit'] for line in lines)
        
        if abs(total_debits - total_credits) > 0.01:
            logger.warning(f"Skipping unbalanced JE: {je.je_id}")
            continue
        
        if action == "approve":
            je.status = "approved"
        elif action == "post":
            je.status = "posted"
            
            # Add to vendor knowledge base
            if je.source_txn_id:
                txn = db.query(TransactionDB).filter(TransactionDB.txn_id == je.source_txn_id).first()
                if txn and lines:
                    # Find the primary expense/revenue account (not Cash at Bank)
                    for line in lines:
                        if "Cash at Bank" not in line['account']:
                            vendor_kb.add_categorization(
                                counterparty=txn.counterparty or "Unknown",
                                description=txn.description,
                                account=line['account'],
                                category="",
                                txn_id=txn.txn_id
                            )
                            break
        
        je.updated_at = datetime.utcnow()
        updated.append(je.je_id)
    
    db.commit()
    
    return {
        "message": f"{action.capitalize()}d {len(updated)} journal entries",
        "updated": updated
    }


@app.get("/api/chart-of-accounts")
async def get_chart_of_accounts():
    """Get the chart of accounts."""
    return {"accounts": CHART_OF_ACCOUNTS}


@app.post("/api/reconcile/run")
async def run_reconciliation(db: Session = Depends(get_db)):
    """
    Run reconciliation to match transactions with journal entries.
    
    Returns reconciliation results and statistics.
    """
    matcher = ReconciliationMatcher(db)
    results = matcher.reconcile_all()
    
    return results


@app.get("/api/reconcile/unmatched")
async def get_unmatched(db: Session = Depends(get_db)):
    """Get unmatched transactions and orphaned journal entries."""
    matcher = ReconciliationMatcher(db)
    
    unmatched_txns = matcher.get_unmatched_transactions()
    orphaned_jes = matcher.get_orphaned_journal_entries()
    
    return {
        "unmatched_transactions": [
            {
                "txn_id": txn.txn_id,
                "date": txn.date.strftime("%Y-%m-%d"),
                "amount": txn.amount,
                "description": txn.description
            }
            for txn in unmatched_txns
        ],
        "orphaned_journal_entries": [
            {
                "je_id": je.je_id,
                "date": je.date.strftime("%Y-%m-%d"),
                "status": je.status,
                "memo": je.memo
            }
            for je in orphaned_jes
        ]
    }


@app.get("/ui/review", response_class=HTMLResponse)
async def review_page(request: Request, db: Session = Depends(get_db)):
    """Render the review page for journal entries."""
    # Get all proposed or approved journal entries
    jes = db.query(JournalEntryDB).filter(
        JournalEntryDB.status.in_(["proposed", "approved"])
    ).order_by(JournalEntryDB.created_at.desc()).all()
    
    # Format entries for template
    entries = []
    for je in jes:
        total_debits = sum(line['debit'] for line in je.lines)
        total_credits = sum(line['credit'] for line in je.lines)
        balance_diff = total_debits - total_credits
        
        entries.append({
            "je_id": je.je_id,
            "date": je.date.strftime("%Y-%m-%d"),
            "lines": je.lines,
            "source_txn_id": je.source_txn_id,
            "memo": je.memo,
            "confidence": je.confidence,
            "status": je.status,
            "needs_review": bool(je.needs_review),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "balance_diff": balance_diff
        })
    
    # Calculate stats
    total = len(entries)
    needs_review = sum(1 for e in entries if e['needs_review'])
    approved = sum(1 for e in entries if e['status'] == 'approved')
    
    return templates.TemplateResponse("review.html", {
        "request": request,
        "entries": entries,
        "total": total,
        "needs_review": needs_review,
        "approved": approved
    })


@app.get("/api/export/journal-entries")
async def export_jes(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Export journal entries to CSV."""
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    export_journal_entries_csv(db, output, status)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=journal_entries_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.get("/api/export/reconciliation")
async def export_recon(db: Session = Depends(get_db)):
    """Export reconciliation results to CSV."""
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    export_reconciliation_csv(db, output)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciliation_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.get("/api/export/general-ledger")
async def export_gl(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export general ledger to CSV."""
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    export_general_ledger_csv(db, output, start_date, end_date)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=general_ledger_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.get("/api/export/trial-balance")
async def export_tb(as_of_date: Optional[str] = None, db: Session = Depends(get_db)):
    """Export trial balance to CSV."""
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    export_trial_balance_csv(db, output, as_of_date)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trial_balance_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.post("/api/export/quickbooks")
async def export_quickbooks(format: str = "iif", status: str = "posted", db: Session = Depends(get_db)):
    """
    Export journal entries to QuickBooks format.
    
    Args:
        format: Export format ('iif' for QuickBooks Desktop, 'csv' for QBO)
        status: Filter by status (posted, approved)
    """
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    
    if format == "iif":
        QuickBooksExporter.export_to_iif(db, output, status)
        media_type = "text/plain"
        filename = f"quickbooks_export_{datetime.now().strftime('%Y%m%d')}.iif"
    else:
        # For now, use same as Xero CSV format
        XeroExporter.export_to_csv(db, output, status)
        media_type = "text/csv"
        filename = f"quickbooks_export_{datetime.now().strftime('%Y%m%d')}.csv"
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/export/xero")
async def export_xero(status: str = "posted", db: Session = Depends(get_db)):
    """Export journal entries to Xero CSV format."""
    from fastapi.responses import StreamingResponse
    
    output = StringIO()
    XeroExporter.export_to_csv(db, output, status)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=xero_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.post("/api/import/quickbooks")
async def import_quickbooks_coa(file: UploadFile = File(...)):
    """
    Import chart of accounts from QuickBooks.
    
    Accepts IIF or CSV format.
    """
    content = (await file.read()).decode('utf-8')
    
    if file.filename.endswith('.iif'):
        accounts = QuickBooksImporter.parse_iif_accounts(content)
    else:
        accounts = QuickBooksImporter.import_from_csv(content)
    
    internal_coa = QuickBooksImporter.map_to_internal_coa(accounts)
    
    return {
        "message": f"Imported {len(accounts)} accounts",
        "accounts": accounts[:10],  # Show first 10
        "internal_chart_of_accounts": internal_coa,
        "total_accounts": len(accounts)
    }


@app.post("/api/import/xero")
async def import_xero_coa(file: UploadFile = File(...)):
    """Import chart of accounts from Xero CSV export."""
    content = (await file.read()).decode('utf-8')
    
    accounts = XeroImporter.import_from_csv(content)
    internal_coa = XeroImporter.map_to_internal_coa(accounts)
    
    return {
        "message": f"Imported {len(accounts)} accounts",
        "accounts": accounts[:10],
        "internal_chart_of_accounts": internal_coa,
        "total_accounts": len(accounts)
    }


@app.get("/api/analytics/pnl")
async def get_pnl(
    company_id: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Get Profit & Loss statement."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    return generate_pnl(db, company_id, start, end)


@app.get("/api/analytics/balance-sheet")
async def get_balance_sheet(
    company_id: str,
    as_of_date: str,
    db: Session = Depends(get_db)
):
    """Get Balance Sheet."""
    as_of = datetime.strptime(as_of_date, "%Y-%m-%d").date()
    
    return generate_balance_sheet(db, company_id, as_of)


@app.get("/api/analytics/cashflow")
async def get_cashflow(
    company_id: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Get Cash Flow statement."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    return generate_cashflow(db, company_id, start, end)


@app.get("/api/analytics/automation-metrics")
async def get_automation_stats(
    company_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get automation performance metrics."""
    return get_automation_metrics(db, company_id, days)


@app.get("/api/analytics/automation-trend")
async def get_trend(
    company_id: str,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Get automation trend over time."""
    return get_automation_trend(db, company_id, days)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check with version."""
    import hashlib
    import sys
    
    # Generate version hash from main file
    version_hash = hashlib.md5(
        f"{sys.version}{datetime.now().date()}".encode()
    ).hexdigest()[:8]
    
    return {
        "status": "healthy",
        "version": f"0.2.0-beta-{version_hash}",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/setup/create-admin")
async def create_admin_user(db: Session = Depends(get_db)):
    """Create admin user for production setup."""
    try:
        from app.db.models import UserDB
        from app.auth.security import get_password_hash
        
        # Check if admin user already exists
        existing = db.query(UserDB).filter(UserDB.email == "admin@example.com").first()
        if existing:
            return {
                "success": True,
                "message": "Admin user already exists",
                "user_id": existing.user_id,
                "email": existing.email,
                "role": existing.role
            }
        
        # Create new admin user
        user_id = f"user-admin-{uuid.uuid4().hex[:8]}"
        password_hash = get_password_hash("admin123")
        
        admin_user = UserDB(
            user_id=user_id,
            email="admin@example.com",
            password_hash=password_hash,
            role="owner",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        return {
            "success": True,
            "message": "Admin user created successfully",
            "user_id": user_id,
            "email": "admin@example.com",
            "password": "admin123",
            "role": "owner"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }



