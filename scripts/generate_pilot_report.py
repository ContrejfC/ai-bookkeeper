#!/usr/bin/env python3
"""
Generate pilot metrics report from simulation results.

Reads from simulation_metrics.json and generates a markdown report.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import CompanyDB, TransactionDB, JournalEntryDB, ReconciliationDB


def generate_pilot_report():
    """Generate pilot metrics report."""
    
    # Read simulation metrics
    metrics_file = Path(__file__).parent.parent / "reports" / "simulation_metrics.json"
    
    if not metrics_file.exists():
        print(f"❌ Metrics file not found: {metrics_file}")
        print("   Run scripts/run_simulation_ingest.py first")
        sys.exit(1)
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    # Generate report
    report_file = Path(__file__).parent.parent / "reports" / "pilot_metrics.md"
    
    with open(report_file, 'w') as f:
        f.write("# AI Bookkeeper - Pilot Simulation Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Simulated Company Performance\n\n")
        
        # Summary table
        f.write("| Company | Txns Ingested | Auto-Approval % | Recon % | Manual Review % | Close Time (mm:ss) |\n")
        f.write("|---------|---------------|-----------------|---------|-----------------|--------------------|\n")
        
        total_txns = 0
        total_auto_approval = 0
        total_recon = 0
        
        for m in metrics:
            company_name = m['company_name']
            txns = m['transactions_ingested']
            auto_approval = m['auto_approval_rate']
            recon = m['reconciliation_rate']
            manual_review = 100 - auto_approval if auto_approval <= 100 else 0
            
            # Convert processing time to mm:ss
            time_seconds = m['ingestion_time_seconds']
            minutes = int(time_seconds // 60)
            seconds = int(time_seconds % 60)
            close_time = f"{minutes:02d}:{seconds:02d}"
            
            f.write(f"| {company_name} | {txns} | {auto_approval:.1f}% | {recon:.1f}% | {manual_review:.1f}% | {close_time} |\n")
            
            total_txns += txns
            total_auto_approval += auto_approval
            total_recon += recon
        
        # Totals/averages
        num_companies = len(metrics)
        avg_auto_approval = total_auto_approval / num_companies
        avg_recon = total_recon / num_companies
        total_time = sum(m['ingestion_time_seconds'] for m in metrics)
        total_minutes = int(total_time // 60)
        total_seconds = int(total_time % 60)
        
        f.write(f"| **TOTAL/AVG** | **{total_txns}** | **{avg_auto_approval:.1f}%** | **{avg_recon:.1f}%** | **{100-avg_auto_approval:.1f}%** | **{total_minutes:02d}:{total_seconds:02d}** |\n\n")
        
        # Key findings
        f.write("## Key Findings\n\n")
        f.write(f"- **Total Transactions Processed:** {total_txns:,}\n")
        f.write(f"- **Average Auto-Approval Rate:** {avg_auto_approval:.1f}%\n")
        f.write(f"- **Average Reconciliation Rate:** {avg_recon:.1f}%\n")
        f.write(f"- **Total Processing Time:** {total_time:.1f} seconds\n")
        f.write(f"- **Companies Tested:** {num_companies}\n\n")
        
        # Detailed metrics per company
        f.write("## Detailed Metrics by Company\n\n")
        
        for m in metrics:
            f.write(f"### {m['company_name']}\n\n")
            f.write(f"- **Transactions Ingested:** {m['transactions_ingested']}\n")
            f.write(f"- **Journal Entries Proposed:** {m['journal_entries_proposed']}\n")
            f.write(f"- **Auto-Approved:** {m['journal_entries_auto_approved']} ({m['auto_approval_rate']:.1f}%)\n")
            f.write(f"- **Needs Review:** {m['journal_entries_needs_review']} ({100-m['auto_approval_rate']:.1f}%)\n")
            f.write(f"- **Posted:** {m['journal_entries_posted']}\n")
            f.write(f"- **Reconciliation Matched:** {m['reconciliation_matched']}\n")
            f.write(f"- **Reconciliation Rate:** {m['reconciliation_rate']:.1f}%\n")
            f.write(f"- **Rules Engine Matches:** {m['rules_engine_matches']}\n")
            f.write(f"- **LLM Categorizations:** {m['llm_categorizations']}\n")
            f.write(f"- **Processing Time:** {m['ingestion_time_seconds']:.2f}s\n")
            
            if m['errors']:
                f.write(f"- **Errors:** {len(m['errors'])}\n")
                for err in m['errors']:
                    f.write(f"  - {err}\n")
            
            f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        if avg_auto_approval < 80:
            f.write("- ⚠️ **Auto-approval rate below target (80%).** Consider:\n")
            f.write("  - Expanding rules engine coverage\n")
            f.write("  - Fine-tuning LLM confidence thresholds\n")
            f.write("  - Adding more historical mappings\n\n")
        else:
            f.write("- ✅ Auto-approval rate meets target (≥80%)\n\n")
        
        if avg_recon < 90:
            f.write("- ⚠️ **Reconciliation rate below target (90%).** Consider:\n")
            f.write("  - Reviewing date tolerance settings\n")
            f.write("  - Improving source transaction ID linking\n")
            f.write("  - Adding fuzzy matching for amounts\n\n")
        else:
            f.write("- ✅ Reconciliation rate meets target (≥90%)\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Review manual review queue for patterns\n")
        f.write("2. Add missing vendor rules to rules engine\n")
        f.write("3. Retrain ML model with approved entries\n")
        f.write("4. Conduct user acceptance testing with pilot clients\n")
    
    print(f"✅ Pilot report generated: {report_file}")
    return report_file


if __name__ == "__main__":
    generate_pilot_report()

