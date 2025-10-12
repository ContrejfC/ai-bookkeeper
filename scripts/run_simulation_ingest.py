#!/usr/bin/env python3
"""
Run full ingestion pipeline for simulated companies.

For each company:
1. Import Chart of Accounts
2. Ingest bank CSV transactions
3. Run categorization (rules → embeddings → LLM)
4. Post journal entries
5. Run reconciliation
6. Collect metrics

Outputs automation metrics per company.
"""
import sys
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import time
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import CompanyDB, TransactionDB, JournalEntryDB, ReconciliationDB, Transaction
from app.ingest.csv_parser import parse_csv_statement
from app.rules.engine import RulesEngine
from app.recon.matcher import ReconciliationMatcher
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def mock_llm_categorize(transaction: Dict, account_list: List[str]) -> Dict[str, Any]:
    """Mock LLM categorization for simulation (no API calls)."""
    # Simple heuristic-based categorization
    desc = transaction["description"].lower()
    amount = transaction["amount"]
    
    # Revenue detection
    if amount > 0:
        if any(word in desc for word in ["square", "stripe", "paypal", "payment"]):
            return {
                "account": "8000 Sales Revenue",
                "confidence": 0.88,
                "needs_review": False,
                "rationale": "Heuristic: Payment processor revenue"
            }
        else:
            return {
                "account": "8000 Sales Revenue",
                "confidence": 0.75,
                "needs_review": False,
                "rationale": "Heuristic: Positive amount (revenue)"
            }
    
    # Expense categorization
    if "aws" in desc or "cloud" in desc or "digital ocean" in desc:
        return {
            "account": "6300 Software Subscriptions",
            "confidence": 0.92,
            "needs_review": False,
            "rationale": "Heuristic: Cloud/SaaS expense"
        }
    elif "ads" in desc or "google" in desc or "facebook" in desc or "marketing" in desc:
        return {
            "account": "7000 Marketing & Advertising",
            "confidence": 0.90,
            "needs_review": False,
            "rationale": "Heuristic: Advertising expense"
        }
    elif "payroll" in desc or "adp" in desc or "paychex" in desc:
        return {
            "account": "6400 Payroll Expenses",
            "confidence": 0.95,
            "needs_review": False,
            "rationale": "Heuristic: Payroll expense"
        }
    elif "utility" in desc or "electric" in desc or "gas" in desc or "water" in desc:
        return {
            "account": "6200 Utilities",
            "confidence": 0.93,
            "needs_review": False,
            "rationale": "Heuristic: Utilities expense"
        }
    elif "amazon" in desc or "office" in desc or "supplies" in desc:
        return {
            "account": "6100 Office Supplies",
            "confidence": 0.85,
            "needs_review": False,
            "rationale": "Heuristic: Office supplies"
        }
    else:
        return {
            "account": "6100 Office Supplies",
            "confidence": 0.70,
            "needs_review": True,
            "rationale": "Heuristic: General expense (low confidence)"
        }


class IngestionMetrics:
    """Track metrics during ingestion."""
    def __init__(self, company_id: str, company_name: str):
        self.company_id = company_id
        self.company_name = company_name
        self.start_time = time.time()
        
        self.txn_count = 0
        self.je_proposed = 0
        self.je_auto_approved = 0
        self.je_needs_review = 0
        self.je_posted = 0
        
        self.recon_matched = 0
        self.recon_unmatched = 0
        
        self.rules_matched = 0
        self.llm_categorized = 0
        
        self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        elapsed = time.time() - self.start_time
        
        auto_approval_rate = (
            (self.je_auto_approved / self.je_proposed * 100)
            if self.je_proposed > 0 else 0.0
        )
        
        recon_rate = (
            (self.recon_matched / self.txn_count * 100)
            if self.txn_count > 0 else 0.0
        )
        
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "transactions_ingested": self.txn_count,
            "journal_entries_proposed": self.je_proposed,
            "journal_entries_auto_approved": self.je_auto_approved,
            "journal_entries_needs_review": self.je_needs_review,
            "journal_entries_posted": self.je_posted,
            "auto_approval_rate": round(auto_approval_rate, 2),
            "reconciliation_matched": self.recon_matched,
            "reconciliation_unmatched": self.recon_unmatched,
            "reconciliation_rate": round(recon_rate, 2),
            "rules_engine_matches": self.rules_matched,
            "llm_categorizations": self.llm_categorized,
            "ingestion_time_seconds": round(elapsed, 2),
            "errors": self.errors
        }


def load_chart_of_accounts(company_id: str, coa_path: Path) -> Dict[str, Any]:
    """Load CoA from metadata file."""
    with open(coa_path, 'r') as f:
        return json.load(f)


def ingest_transactions(db, company_id: str, csv_files: List[Path], metrics: IngestionMetrics):
    """Ingest transactions from CSV files with per-file error isolation."""
    logger.info(f"  📥 Ingesting transactions from {len(csv_files)} CSV files...")
    
    for csv_file in sorted(csv_files):
        file_success = False
        try:
            # Parse CSV (returns Transaction Pydantic models)
            transactions = parse_csv_statement(str(csv_file))
            logger.info(f"    {csv_file.name}: {len(transactions)} transactions")
            
            # Insert into database
            for txn in transactions:
                # Convert date string to date object
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
                    txn_id = f"txn_{company_id}_{uuid.uuid4().hex[:16]}"
                    txn_db = TransactionDB(
                        txn_id=txn_id,
                        company_id=company_id,
                        date=txn_date,
                        amount=txn.amount,
                        currency=txn.currency,
                        description=txn.description,
                        counterparty=txn.counterparty or "",
                        raw=txn.raw or {}
                    )
                    db.add(txn_db)
                    metrics.txn_count += 1
            
            # Flush this file's transactions
            db.flush()
            file_success = True
            
        except Exception as e:
            # Roll back only this file's work
            db.rollback()
            error_msg = f"{csv_file.name}: {str(e)}"
            logger.error(f"    ❌ {error_msg}")
            metrics.errors.append(error_msg)
            
            # Log to error file
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            error_log = log_dir / "ingest_errors.log"
            
            with open(error_log, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] company={company_id}, file={csv_file.name}, error={str(e)}\n")
            
            continue  # Skip to next file
    
    # Commit all successful files
    db.commit()
    logger.info(f"  ✓ Ingested {metrics.txn_count} unique transactions")


def categorize_transactions(db, company_id: str, coa: List[Dict], metrics: IngestionMetrics):
    """Categorize transactions and create journal entries."""
    logger.info(f"  🤖 Categorizing transactions...")
    
    # Initialize rules engine
    rules_engine = RulesEngine()
    
    # Load uncategorized transactions
    transactions = db.query(TransactionDB).filter(
        TransactionDB.company_id == company_id
    ).all()
    
    # Extract account names for LLM
    account_list = [f"{a['account_num']} {a['account_name']}" for a in coa]
    
    for txn in transactions:
        # Check if JE already exists
        existing_je = db.query(JournalEntryDB).filter(
            JournalEntryDB.source_txn_id == txn.txn_id
        ).first()
        
        if existing_je:
            continue
        
        try:
            # Step 1: Try rules engine
            # Convert TransactionDB to Transaction model for rules engine
            txn_model = Transaction(
                txn_id=txn.txn_id,
                date=str(txn.date),
                amount=txn.amount,
                currency=txn.currency,
                description=txn.description,
                counterparty=txn.counterparty or "",
                raw=txn.raw or {},
                doc_ids=[]
            )
            
            rule_result = rules_engine.match_transaction(txn_model)
            
            if rule_result and rule_result.get("matched", False):
                metrics.rules_matched += 1
                category = rule_result["account"]
                confidence = 0.95
                needs_review = False
                rationale = rule_result.get("rationale", "Rules engine match")
            else:
                # Step 2: Mock LLM categorization (no API calls for simulation)
                result = mock_llm_categorize(
                    {
                        "txn_id": txn.txn_id,
                        "date": str(txn.date),
                        "amount": txn.amount,
                        "description": txn.description,
                        "counterparty": txn.counterparty,
                        "currency": txn.currency
                    },
                    account_list
                )
                
                metrics.llm_categorized += 1
                category = result.get("account", "6100 Office Supplies")
                confidence = result.get("confidence", 0.75)
                needs_review = result.get("needs_review", False)
                rationale = result.get("rationale", "LLM categorization")
            
            # Create balanced journal entry
            if txn.amount > 0:
                # Receipt: Debit Cash, Credit Revenue
                lines = [
                    {"account": "1000 Cash at Bank", "debit": txn.amount, "credit": 0.0},
                    {"account": category, "debit": 0.0, "credit": txn.amount}
                ]
            else:
                # Payment: Debit Expense, Credit Cash
                lines = [
                    {"account": category, "debit": abs(txn.amount), "credit": 0.0},
                    {"account": "1000 Cash at Bank", "debit": 0.0, "credit": abs(txn.amount)}
                ]
            
            # Determine status
            if needs_review or confidence < 0.85:
                status = "proposed"
                metrics.je_needs_review += 1
            else:
                status = "approved"
                metrics.je_auto_approved += 1
            
            # Save journal entry with UUID
            je_id = f"je_{company_id}_{uuid.uuid4().hex[:16]}"
            je = JournalEntryDB(
                je_id=je_id,
                company_id=company_id,
                date=txn.date,
                lines=lines,
                source_txn_id=txn.txn_id,
                memo=rationale,
                confidence=confidence,
                status=status
            )
            db.add(je)
            metrics.je_proposed += 1
            
            # Auto-post if approved
            if status == "approved":
                je.status = "posted"
                metrics.je_posted += 1
        
        except Exception as e:
            error_msg = f"Error categorizing txn {txn.txn_id}: {e}"
            logger.error(f"    ❌ {error_msg}")
            metrics.errors.append(error_msg)
    
    db.commit()
    logger.info(f"  ✓ Created {metrics.je_proposed} journal entries")
    
    if metrics.je_proposed > 0:
        logger.info(f"    Auto-approved: {metrics.je_auto_approved} ({metrics.je_auto_approved/metrics.je_proposed*100:.1f}%)")
        logger.info(f"    Needs review: {metrics.je_needs_review} ({metrics.je_needs_review/metrics.je_proposed*100:.1f}%)")


def run_reconciliation(db, company_id: str, metrics: IngestionMetrics):
    """Run reconciliation matching."""
    logger.info(f"  🔗 Running reconciliation...")
    
    try:
        matcher = ReconciliationMatcher(db)
        results = matcher.reconcile_all()
        
        stats = results.get("statistics", {})
        metrics.recon_matched = stats.get("matched", 0)
        metrics.recon_unmatched = stats.get("unmatched_transactions", 0)
        
        logger.info(f"  ✓ Matched: {metrics.recon_matched}, Unmatched: {metrics.recon_unmatched}")
        
        if (metrics.recon_matched + metrics.recon_unmatched) > 0:
            match_rate = metrics.recon_matched / (metrics.recon_matched + metrics.recon_unmatched) * 100
            logger.info(f"    Match rate: {match_rate:.1f}%")
    
    except Exception as e:
        error_msg = f"Reconciliation error: {e}"
        logger.error(f"  ❌ {error_msg}")
        metrics.errors.append(error_msg)


def process_company(company_id: str, company_name: str, data_dir: Path) -> Dict[str, Any]:
    """Process a single company through full pipeline."""
    logger.info(f"\n{'='*70}")
    logger.info(f"🏢 {company_name}")
    logger.info(f"{'='*70}")
    
    metrics = IngestionMetrics(company_id, company_name)
    
    # Find company data
    company_short_id = company_id.replace("sim_", "")
    csv_dir = data_dir / "simulated_csv" / company_short_id
    metadata_dir = data_dir / "simulated_metadata" / company_short_id
    
    if not csv_dir.exists() or not metadata_dir.exists():
        logger.error(f"  ❌ Data not found for {company_id}")
        return metrics.to_dict()
    
    with get_db_context() as db:
        # 1. Load CoA
        coa_path = metadata_dir / "coa.json"
        logger.info(f"  📋 Loading chart of accounts...")
        coa = load_chart_of_accounts(company_id, coa_path)
        logger.info(f"  ✓ Loaded {len(coa)} accounts")
        
        # 2. Ingest transactions
        csv_files = sorted(csv_dir.glob("bank_*.csv"))
        ingest_transactions(db, company_id, csv_files, metrics)
        
        # 3. Categorize & post
        categorize_transactions(db, company_id, coa, metrics)
        
        # 4. Reconciliation
        run_reconciliation(db, company_id, metrics)
    
    logger.info(f"\n📊 Summary for {company_name}:")
    logger.info(f"  Transactions: {metrics.txn_count}")
    logger.info(f"  Auto-approval rate: {metrics.to_dict()['auto_approval_rate']}%")
    logger.info(f"  Reconciliation rate: {metrics.to_dict()['reconciliation_rate']}%")
    logger.info(f"  Time: {metrics.to_dict()['ingestion_time_seconds']}s")
    
    return metrics.to_dict()


def main():
    """Run ingestion for all simulated companies."""
    logger.info("="*70)
    logger.info("🚀 SIMULATION INGESTION PIPELINE")
    logger.info("="*70)
    
    data_dir = Path(__file__).parent.parent / "data"
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all companies - extract data before session closes
    with get_db_context() as db:
        companies_raw = db.query(CompanyDB).filter(
            CompanyDB.company_id.like("sim_%")
        ).all()
        
        # Copy company data before session closes
        companies = [(c.company_id, c.company_name) for c in companies_raw]
    
    logger.info(f"\nFound {len(companies)} simulated companies\n")
    
    all_metrics = []
    
    for company_id, company_name in companies:
        try:
            metrics = process_company(company_id, company_name, data_dir)
            all_metrics.append(metrics)
        except Exception as e:
            logger.error(f"❌ Failed to process {company_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save aggregated metrics
    metrics_file = output_dir / "simulation_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ INGESTION COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"\n📊 Aggregate Metrics:")
    
    total_txns = sum(m["transactions_ingested"] for m in all_metrics)
    avg_auto_approval = (
        sum(m["auto_approval_rate"] for m in all_metrics) / len(all_metrics)
        if all_metrics else 0.0
    )
    avg_recon = (
        sum(m["reconciliation_rate"] for m in all_metrics) / len(all_metrics)
        if all_metrics else 0.0
    )
    total_time = sum(m["ingestion_time_seconds"] for m in all_metrics)
    
    logger.info(f"  Companies processed: {len(all_metrics)}")
    logger.info(f"  Total transactions: {total_txns}")
    logger.info(f"  Avg auto-approval rate: {avg_auto_approval:.1f}%")
    logger.info(f"  Avg reconciliation rate: {avg_recon:.1f}%")
    logger.info(f"  Total processing time: {total_time:.1f}s")
    logger.info(f"\n💾 Metrics saved to: {metrics_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

