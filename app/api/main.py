"""FastAPI application main entry point."""
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Response
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
from app.auth.security import get_company_id_from_token, require_role, get_current_user
from config.settings import settings
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Bookkeeper",
    description="AI-powered bookkeeping with automated journal entry posting",
    version="0.2.1-beta",
    servers=[{"url": "https://api.ai-bookkeeper.app", "description": "Production"}]
)

# ============================================================================
# CORS Configuration
# ============================================================================
import os
from fastapi.middleware.cors import CORSMiddleware

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://app.ai-bookkeeper.app,https://ai-bookkeeper-web.onrender.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
logger.info(f"✅ CORS enabled for origins: {ALLOWED_ORIGINS}")

# ============================================================================
# P1.1 Security Patch: CSRF Protection Middleware
# ============================================================================
from app.auth.csrf import csrf_protect

# Add CSRF middleware
app.middleware("http")(csrf_protect)
logger.info("✅ CSRF protection middleware enabled")

# ============================================================================
# API Key Authentication Middleware (runs before entitlement checks)
# ============================================================================
try:
    from app.middleware.api_key_auth import APIKeyAuthMiddleware
    app.add_middleware(APIKeyAuthMiddleware)
    logger.info("✅ API key authentication middleware enabled")
except ImportError as e:
    logger.warning(f"⚠️  API key auth middleware not available: {e}")

# ============================================================================
# Billing Entitlement Middleware
# ============================================================================
try:
    from app.middleware.entitlements import EntitlementGateMiddleware
    app.add_middleware(EntitlementGateMiddleware)
    logger.info("✅ Entitlement gate middleware enabled")
except ImportError as e:
    logger.warning(f"⚠️  Entitlement middleware not available: {e}")

# ============================================================================
# Wave-2 Phase 1, 2a & 2b: Import and register API routes
# ============================================================================
try:
    from app.api import tenants, auth as wave2_auth, rules, audit_export, billing, billing_v2, notifications, receipts, analytics as analytics_api, tools, post_idempotency, background_jobs
    from app.api import onboarding as onboarding_api
    # from app.ui import routes as ui_routes  # DISABLED: Next.js serves UI pages
    from app.routers import qbo as qbo_router, actions as actions_router, privacy as privacy_router
    
    # Include Phase 1 routers
    app.include_router(wave2_auth.router)
    app.include_router(tenants.router)
    app.include_router(rules.router)
    app.include_router(audit_export.router)
    app.include_router(background_jobs.router)  # Background jobs API
    app.include_router(onboarding_api.router)  # Onboarding API
    
    # Include Phase 2a routers
    app.include_router(billing.router)  # Original billing
    app.include_router(billing_v2.router, prefix="/v2")  # Enhanced billing with ad-ready pricing
    app.include_router(notifications.router)
    
    # Include Phase 2b routers
    app.include_router(onboarding.router)
    app.include_router(receipts.router)
    app.include_router(analytics_api.router)
    
    # Include Tools router (CSV cleaner, etc.)
    app.include_router(tools.router)
    
    # Include Post idempotency router
    app.include_router(post_idempotency.router)
    
    # Include QBO integration router
    app.include_router(qbo_router.router)
    
    # Include GPT Actions router
    app.include_router(actions_router.router)
    
    # Include Privacy router
    app.include_router(privacy_router.router)
    
    # ============================================================================
    # UI Routes: DISABLED to allow Next.js frontend to serve pages
    # ============================================================================
    # The Jinja2 landing page conflicts with Next.js frontend routing.
    # Next.js will serve all pages (/, /pricing, /dashboard, etc.)
    # API endpoints remain accessible at /api/* and /docs
    # 
    # app.include_router(ui_routes.router, tags=["ui"])
    # 
    # # Mount static files for UI
    # try:
    #     app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
    # except:
    #     pass  # Static directory may not exist in all environments
    
    logger.info("✅ Wave-2 Phase 1, 2a & 2b routes loaded successfully")
    logger.info("✅ QBO integration routes loaded")
    logger.info("✅ GPT Actions discovery route loaded")
    logger.info("✅ Privacy & training data routes loaded")
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

# === Slim OpenAPI for GPT Actions (≤30 operations) ============================
import os
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# Public base URL for the service (override in Render env if you want)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://api.ai-bookkeeper.app")

# Only expose endpoints GPT needs
ALLOWED_GPT_PATHS = [
    "/actions",
    "/api/billing/status",
    "/api/billing/create_checkout_session",
    "/api/billing/portal_link",
    "/api/auth/qbo/start",
    "/api/qbo/status",
    "/api/post/propose",
    "/api/post/commit",
]

@app.get("/openapi.gpt.json", include_in_schema=False)
def openapi_for_gpt():
    """
    A slim schema for ChatGPT Actions. Keeps total operations well under 30,
    declares Bearer auth, and sets the required `servers` array.
    """
    schema = get_openapi(
        title="AI Bookkeeper – GPT Actions",
        version="1.0.0",
        description="Slimmed schema for ChatGPT Actions (≤30 operations).",
        routes=app.routes,
    )

    # Keep only the whitelisted paths
    schema["paths"] = {p: v for p, v in schema.get("paths", {}).items() if p in ALLOWED_GPT_PATHS}

    # Required by GPT Actions
    schema["servers"] = [{"url": PUBLIC_BASE_URL, "description": "Production"}]

    # Bearer auth to match GPT Action config (API Key → Bearer)
    schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(
        {"BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "Token"}}
    )
    schema["security"] = [{"BearerAuth": []}]

    # Fix GPT Actions validation issues
    for path, path_obj in schema["paths"].items():
        for method, operation in path_obj.items():
            # Truncate descriptions to 300 chars max
            if "description" in operation and len(operation["description"]) > 300:
                operation["description"] = operation["description"][:297] + "..."
            
            # Remove problematic parameters (header/cookie locations)
            if "parameters" in operation:
                operation["parameters"] = [
                    p for p in operation["parameters"] 
                    if p.get("in") not in ["header", "cookie"]
                ]
            
            # Fix request body schemas
            if "requestBody" in operation:
                request_body = operation["requestBody"]
                if "content" in request_body:
                    for content_type, content_obj in request_body["content"].items():
                        if "schema" in content_obj:
                            schema_obj = content_obj["schema"]
                            # Ensure schema is an object type
                            if schema_obj.get("type") != "object":
                                schema_obj["type"] = "object"
                                schema_obj["properties"] = schema_obj.get("properties", {})
                                schema_obj["required"] = schema_obj.get("required", [])

    return JSONResponse(schema)
# =============================================================================

# Create tables
# NOTE: Disabled in production - use Alembic migrations instead
# In production/Cloud Run, database tables should be created via:
#   alembic upgrade head
# Uncomment below only for local development if needed:
# Base.metadata.create_all(bind=engine)

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
    request: Request,
    response: Response,
    txn_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate proposed journal entries for transactions.
    
    Uses tiered decisioning: rules → embeddings → LLM → human review
    
    Idempotency:
    -----------
    - Send `Idempotency-Key` header to prevent duplicate processing
    - If same key is received within 24 hours, cached result is returned
    - Key format: any unique string (e.g., UUID)
    
    Entitlements:
    ------------
    - Checks transaction quota
    - Returns quota headers in response
    - 402 if quota exceeded
    """
    # Check entitlements
    from app.middleware.entitlements import check_entitlements, add_quota_headers, log_usage
    entitlements = await check_entitlements(request, current_user, db, enforce_quota=True)
    
    # Get tenant_id
    tenant_ids = current_user.tenant_ids if hasattr(current_user, 'tenant_ids') else []
    tenant_id = tenant_ids[0] if isinstance(tenant_ids, list) and tenant_ids else None
    
    # Check idempotency
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        # Check if we've processed this request before
        from app.db.models import IdempotencyLogDB
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        existing = db.query(IdempotencyLogDB).filter(
            IdempotencyLogDB.idempotency_key == idempotency_key,
            IdempotencyLogDB.endpoint == "/api/post/propose",
            IdempotencyLogDB.created_at >= cutoff
        ).first()
        
        if existing:
            logger.info(f"Idempotent request detected: {idempotency_key}")
            # Return cached response
            add_quota_headers(response, entitlements)
            return existing.response_data
    
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
    
    # Log usage for quota tracking
    if tenant_id:
        log_usage(tenant_id, "propose", len(proposed_jes), db)
    
    # Prepare response
    result = {
        "message": f"Proposed {len(proposed_jes)} journal entries",
        "proposed": proposed_jes,
        "review_needed": sum(1 for je in proposed_jes if je.get('needs_review'))
    }
    
    # Store idempotency record
    if idempotency_key:
        from app.db.models import IdempotencyLogDB
        idempotency_log = IdempotencyLogDB(
            idempotency_key=idempotency_key,
            endpoint="/api/post/propose",
            response_data=result,
            created_at=datetime.utcnow()
        )
        db.add(idempotency_log)
        db.commit()
    
    # Add quota headers
    add_quota_headers(response, entitlements)
    
    return result


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


@app.post("/api/post/commit")
async def commit_journal_entries(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Commit approved journal entries to QuickBooks Online with idempotency.
    
    Request body:
    {
        "approvals": [
            {
                "txn_id": "t1",
                "je": {
                    "txnDate": "2025-10-16",
                    "refNumber": "AB-1001",
                    "privateNote": "AI Bookkeeper",
                    "lines": [
                        {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
                        {"amount": 150.00, "postingType": "Credit", "accountRef": {"value": "7"}}
                    ]
                }
            }
        ]
    }
    
    Response:
    {
        "results": [
            {"txn_id": "t1", "qbo_doc_id": "123", "idempotent": false, "status": "posted"},
            {"txn_id": "t2", "error": {"code": "UNBALANCED_JE", "message": "..."}, "status": "error"}
        ]
    }
    
    Errors (global):
    - 402 ENTITLEMENT_REQUIRED - If no active subscription or over monthly cap
    - 429 FREE_CAP_EXCEEDED - Should not apply to commit (only propose)
    
    Errors (per-item):
    - UNBALANCED_JE - Debits != credits
    - QBO_VALIDATION - QBO rejected entry
    - QBO_UPSTREAM - QBO API unavailable
    - QBO_UNAUTHORIZED - QBO not connected
    """
    from app.services.qbo import QBOService
    from app.services.billing import BillingService
    
    # Parse request body
    body = await request.json()
    approvals = body.get("approvals", [])
    
    if not approvals:
        raise HTTPException(status_code=400, detail="No approvals provided")
    
    # Get tenant ID from request state (set by middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # Fallback: extract from auth or default
        # For now, use a placeholder - production should set this via middleware
        tenant_id = body.get("tenant_id", "default_tenant")
    
    # Initialize services
    qbo_service = QBOService(db)
    billing_service = BillingService(db)
    
    results = []
    posted_count = 0
    
    for approval in approvals:
        txn_id = approval.get("txn_id")
        je_payload = approval.get("je")
        
        if not je_payload:
            results.append({
                "txn_id": txn_id,
                "status": "error",
                "error": {
                    "code": "MISSING_JE_PAYLOAD",
                    "message": "Journal entry payload is required"
                }
            })
            continue
        
        try:
            # Post to QBO with idempotency
            result = await qbo_service.post_idempotent_je(tenant_id, je_payload)
            
            results.append({
                "txn_id": txn_id,
                "qbo_doc_id": result["qbo_doc_id"],
                "idempotent": result["idempotent"],
                "status": "posted"
            })
            
            # Increment posted count only for non-idempotent posts
            if not result["idempotent"]:
                posted_count += 1
            
        except ValueError as e:
            # Balance validation error
            error_str = str(e)
            if "UNBALANCED_JE" in error_str:
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "UNBALANCED_JE",
                        "message": error_str.replace("UNBALANCED_JE:", "")
                    }
                })
            else:
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(e)
                    }
                })
        
        except Exception as e:
            # Map QBO errors to item-level errors
            error_str = str(e)
            
            if "QBO_NOT_CONNECTED" in error_str or "QBO_UNAUTHORIZED" in error_str:
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "QBO_UNAUTHORIZED",
                        "message": "QuickBooks not connected. Please connect your QuickBooks account."
                    }
                })
            elif "QBO_VALIDATION" in error_str:
                safe_message = error_str.replace("QBO_VALIDATION:", "").strip()
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "QBO_VALIDATION",
                        "message": safe_message
                    }
                })
            elif "QBO_UPSTREAM" in error_str or "QBO_RATE_LIMITED" in error_str:
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "QBO_UPSTREAM",
                        "message": "QuickBooks API unavailable. Please try again shortly."
                    }
                })
            else:
                logger.error(f"Unexpected error posting JE for txn {txn_id}: {e}")
                results.append({
                    "txn_id": txn_id,
                    "status": "error",
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Failed to post journal entry. Please try again."
                    }
                })
    
    # Increment posted count in usage (only for new posts, not idempotent)
    if posted_count > 0:
        try:
            billing_service.increment_posted(tenant_id, count=posted_count)
        except Exception as e:
            logger.error(f"Failed to increment posted count: {e}")
    
    # Return 200 with per-item results (even if some failed)
    return {
        "results": results,
        "summary": {
            "total": len(approvals),
            "posted": sum(1 for r in results if r["status"] == "posted"),
            "errors": sum(1 for r in results if r["status"] == "error")
        }
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



