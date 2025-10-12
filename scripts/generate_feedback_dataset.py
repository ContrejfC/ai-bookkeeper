#!/usr/bin/env python3
"""
Generate training dataset CSV from approved journal entries.

Creates a CSV file suitable for ML model training with:
- Transaction details
- Predicted account
- Approved account  
- Confidence scores
- Review outcomes
"""
import sys
import csv
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import TransactionDB, JournalEntryDB


def generate_training_dataset():
    """Generate training.csv from database."""
    
    output_dir = Path(__file__).parent.parent / "data" / "feedback"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "training.csv"
    
    with get_db_context() as db:
        # Query all journal entries with their source transactions
        query = db.query(JournalEntryDB, TransactionDB).join(
            TransactionDB,
            JournalEntryDB.source_txn_id == TransactionDB.txn_id
        ).order_by(JournalEntryDB.company_id, JournalEntryDB.date)
        
        results = query.all()
        
        if not results:
            print("❌ No journal entries found in database")
            print("   Run scripts/run_simulation_ingest.py first")
            sys.exit(1)
        
        # Write CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'company_id',
                'txn_id',
                'date',
                'amount',
                'description',
                'counterparty',
                'predicted_account',
                'approved_account',
                'confidence',
                'review_outcome'
            ])
            
            # Data rows
            for je, txn in results:
                # Extract predicted account (first non-cash account in JE lines)
                predicted_account = "Unknown"
                approved_account = "Unknown"
                
                for line in je.lines:
                    account = line.get('account', '')
                    if 'Cash at Bank' not in account:
                        predicted_account = account
                        approved_account = account  # Same for now (simulated data)
                        break
                
                # Determine review outcome based on status
                if je.status == 'posted':
                    review_outcome = 'approved'
                elif je.status == 'approved':
                    review_outcome = 'approved'
                elif je.status == 'proposed':
                    if je.needs_review:
                        review_outcome = 'needs_review'
                    else:
                        review_outcome = 'proposed'
                else:
                    review_outcome = je.status
                
                writer.writerow([
                    je.company_id,
                    txn.txn_id,
                    txn.date.strftime('%Y-%m-%d'),
                    f"{txn.amount:.2f}",
                    txn.description,
                    txn.counterparty or '',
                    predicted_account,
                    approved_account,
                    f"{je.confidence:.4f}",
                    review_outcome
                ])
        
        print(f"✅ Training dataset generated: {output_file}")
        print(f"   Total records: {len(results):,}")
        
        # Show first 5 rows
        print(f"\n📊 Sample (first 5 rows):")
        print(f"{'='*100}")
        
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Print header
            print(f"{header[0]:<25} {header[1]:<35} {header[2]:<12} {header[3]:<10} {header[6]:<30}")
            print(f"{'-'*25} {'-'*35} {'-'*12} {'-'*10} {'-'*30}")
            
            # Print first 5 data rows
            for i, row in enumerate(reader):
                if i >= 5:
                    break
                # Truncate long fields for display
                company = row[0][:24]
                txn_id = row[1][:34]
                date = row[2]
                amount = row[3][:9]
                account = row[6][:29]
                
                print(f"{company:<25} {txn_id:<35} {date:<12} ${amount:<9} {account:<30}")
        
        print(f"{'='*100}\n")
        
        return output_file


if __name__ == "__main__":
    generate_training_dataset()

