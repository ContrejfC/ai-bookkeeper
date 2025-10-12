"""Background tasks for async job processing."""
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import tempfile
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import get_db_context
from app.db.models import TransactionDB, JournalEntryDB, CompanyDB
from app.ingest.csv_parser import parse_csv_statement
from app.worker.queue import update_job_progress
from rq import get_current_job

logger = logging.getLogger(__name__)

# Chunk size for batching
CHUNK_SIZE = 500


def ingest_batch(
    company_id: str,
    csv_content: str,
    filename: str = "upload.csv"
) -> Dict[str, Any]:
    """
    Ingest transactions from CSV file.
    
    Args:
        company_id: Company identifier
        csv_content: CSV file content as string
        filename: Original filename
        
    Returns:
        Dict with ingestion results
    """
    job = get_current_job()
    logger.info(f"Starting CSV ingestion for company {company_id}")
    
    start_time = time.time()
    result = {
        "company_id": company_id,
        "filename": filename,
        "transactions_parsed": 0,
        "transactions_ingested": 0,
        "errors": [],
        "started_at": datetime.now().isoformat()
    }
    
    try:
        # Write CSV to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = f.name
        
        # Parse CSV
        update_job_progress(job.id, 10, "Parsing CSV...")
        transactions = parse_csv_statement(temp_path)
        result['transactions_parsed'] = len(transactions)
        
        # Chunk transactions
        chunks = [transactions[i:i + CHUNK_SIZE] for i in range(0, len(transactions), CHUNK_SIZE)]
        
        # Ingest chunks
        with get_db_context() as db:
            for idx, chunk in enumerate(chunks):
                progress = 10 + int((idx / len(chunks)) * 80)
                update_job_progress(job.id, progress, f"Ingesting chunk {idx+1}/{len(chunks)}...")
                
                for txn in chunk:
                    try:
                        # Convert date
                        if isinstance(txn.date, str):
                            txn_date = datetime.strptime(txn.date, "%Y-%m-%d").date()
                        else:
                            txn_date = txn.date
                        
                        # Check if exists
                        existing = db.query(TransactionDB).filter(
                            TransactionDB.company_id == company_id,
                            TransactionDB.date == txn_date,
                            TransactionDB.amount == txn.amount,
                            TransactionDB.description == txn.description
                        ).first()
                        
                        if not existing:
                            txn_db = TransactionDB(
                                txn_id=txn.txn_id,
                                company_id=company_id,
                                date=txn_date,
                                amount=txn.amount,
                                currency=txn.currency,
                                description=txn.description,
                                counterparty=txn.counterparty or "",
                                raw=txn.raw or {}
                            )
                            db.add(txn_db)
                            result['transactions_ingested'] += 1
                            
                    except Exception as e:
                        error_msg = f"Transaction error: {str(e)}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                
                db.commit()
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        
        # Final progress
        update_job_progress(job.id, 100, "Ingestion complete")
        
        result['finished_at'] = datetime.now().isoformat()
        result['duration_seconds'] = time.time() - start_time
        
        logger.info(f"Ingestion complete: {result['transactions_ingested']} transactions")
        return result
        
    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
        result['finished_at'] = datetime.now().isoformat()
        raise


def post_propose_batch(
    company_id: str,
    limit: int = 100,
    use_ml: bool = True
) -> Dict[str, Any]:
    """
    Generate posting proposals for unposted transactions.
    
    Args:
        company_id: Company identifier
        limit: Maximum transactions to process
        use_ml: Whether to use ML classifier
        
    Returns:
        Dict with proposal results
    """
    job = get_current_job()
    logger.info(f"Starting posting proposals for company {company_id}")
    
    start_time = time.time()
    result = {
        "company_id": company_id,
        "transactions_processed": 0,
        "proposals_created": 0,
        "auto_approved": 0,
        "needs_review": 0,
        "started_at": datetime.now().isoformat()
    }
    
    try:
        # Import decision engine
        from app.decision.engine import DecisionEngine
        
        engine = DecisionEngine(use_ml=use_ml, use_llm=False)  # Mock LLM for now
        
        with get_db_context() as db:
            # Get unposted transactions
            update_job_progress(job.id, 10, "Fetching transactions...")
            
            transactions = db.query(TransactionDB).filter(
                TransactionDB.company_id == company_id
            ).limit(limit).all()
            
            total = len(transactions)
            
            # Process each transaction
            for idx, txn in enumerate(transactions):
                progress = 10 + int((idx / total) * 80)
                update_job_progress(job.id, progress, f"Processing {idx+1}/{total}...")
                
                # Check if already has JE
                existing_je = db.query(JournalEntryDB).filter(
                    JournalEntryDB.source_txn_id == txn.txn_id
                ).first()
                
                if existing_je:
                    continue
                
                # Get decision
                decision = engine.categorize(
                    amount=txn.amount,
                    description=txn.description,
                    counterparty=txn.counterparty or "",
                    date=txn.date
                )
                
                # Create JE
                lines = [
                    {"account": decision['account'], "debit": abs(txn.amount) if txn.amount < 0 else 0, "credit": txn.amount if txn.amount > 0 else 0},
                    {"account": "1000 Cash at Bank", "debit": txn.amount if txn.amount > 0 else 0, "credit": abs(txn.amount) if txn.amount < 0 else 0}
                ]
                
                je = JournalEntryDB(
                    je_id=f"je_{company_id}_{txn.txn_id[:16]}",
                    company_id=company_id,
                    date=txn.date,
                    lines=lines,
                    source_txn_id=txn.txn_id,
                    memo=decision.get('rationale', ''),
                    confidence=decision.get('confidence', 0.0),
                    status='approved' if decision.get('confidence', 0) >= 0.85 else 'proposed',
                    needs_review=decision.get('needs_review', False)
                )
                
                db.add(je)
                result['proposals_created'] += 1
                
                if je.status == 'approved':
                    result['auto_approved'] += 1
                else:
                    result['needs_review'] += 1
                
                result['transactions_processed'] += 1
            
            db.commit()
        
        # Final progress
        update_job_progress(job.id, 100, "Proposals complete")
        
        result['finished_at'] = datetime.now().isoformat()
        result['duration_seconds'] = time.time() - start_time
        
        logger.info(f"Proposals complete: {result['proposals_created']} created")
        return result
        
    except Exception as e:
        error_msg = f"Proposal generation failed: {str(e)}"
        logger.error(error_msg)
        raise


def reconcile_batch(
    company_id: str
) -> Dict[str, Any]:
    """
    Run reconciliation for a company.
    
    Args:
        company_id: Company identifier
        
    Returns:
        Dict with reconciliation results
    """
    job = get_current_job()
    logger.info(f"Starting reconciliation for company {company_id}")
    
    start_time = time.time()
    result = {
        "company_id": company_id,
        "matches_created": 0,
        "started_at": datetime.now().isoformat()
    }
    
    try:
        update_job_progress(job.id, 10, "Initializing reconciliation...")
        
        from app.recon.matcher import ReconciliationMatcher
        
        with get_db_context() as db:
            matcher = ReconciliationMatcher(db)
            
            update_job_progress(job.id, 50, "Running reconciliation...")
            
            matches = matcher.reconcile_all(company_id)
            result['matches_created'] = len(matches)
            
            db.commit()
        
        # Final progress
        update_job_progress(job.id, 100, "Reconciliation complete")
        
        result['finished_at'] = datetime.now().isoformat()
        result['duration_seconds'] = time.time() - start_time
        
        logger.info(f"Reconciliation complete: {result['matches_created']} matches")
        return result
        
    except Exception as e:
        error_msg = f"Reconciliation failed: {str(e)}"
        logger.error(error_msg)
        raise

