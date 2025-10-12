#!/usr/bin/env python3
"""
Test ML classifier automation rate on simulated tenants.

Re-runs categorization using the hybrid decision engine with ML enabled.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import TransactionDB, JournalEntryDB, CompanyDB
from app.decision.engine import DecisionEngine

def test_ml_automation():
    """Test automation rate with ML classifier."""
    print("\n" + "="*70)
    print("  ML CLASSIFIER AUTOMATION TEST")
    print("="*70)
    
    # Initialize decision engine with ML enabled
    engine = DecisionEngine(
        use_rules=True,
        use_ml=True,
        use_llm=False,
        ml_threshold=0.85
    )
    
    # Test on all simulated companies
    results = {}
    
    with get_db_context() as db:
        companies = db.query(CompanyDB).filter(
            CompanyDB.company_id.like('sim_%')
        ).all()
        
        print(f"\n📊 Testing {len(companies)} companies...\n")
        
        for company in companies:
            print(f"🏢 {company.company_name}")
            
            # Get transactions
            transactions = db.query(TransactionDB).filter(
                TransactionDB.company_id == company.company_id
            ).limit(100).all()  # Sample 100 transactions
            
            total = len(transactions)
            auto_approved = 0
            needs_review = 0
            
            method_counts = {'rules': 0, 'ml': 0, 'ml_review': 0, 'fallback': 0}
            
            # Test each transaction
            for txn in transactions:
                decision = engine.categorize(
                    amount=txn.amount,
                    description=txn.description,
                    counterparty=txn.counterparty or "",
                    date=txn.date
                )
                
                if decision['needs_review']:
                    needs_review += 1
                else:
                    auto_approved += 1
                
                method = decision['method']
                method_counts[method] = method_counts.get(method, 0) + 1
            
            auto_approval_rate = (auto_approved / total * 100) if total > 0 else 0
            
            results[company.company_name] = {
                'total': total,
                'auto_approved': auto_approved,
                'needs_review': needs_review,
                'rate': auto_approval_rate,
                'methods': method_counts
            }
            
            print(f"   Transactions: {total}")
            print(f"   Auto-approved: {auto_approved} ({auto_approval_rate:.1f}%)")
            print(f"   Needs review: {needs_review} ({needs_review/total*100:.1f}%)")
            print(f"   Methods: Rules={method_counts['rules']}, ML={method_counts['ml']}, ML(review)={method_counts['ml_review']}, Fallback={method_counts['fallback']}")
            print()
    
    # Aggregate results
    total_txns = sum(r['total'] for r in results.values())
    total_auto_approved = sum(r['auto_approved'] for r in results.values())
    overall_rate = (total_auto_approved / total_txns * 100) if total_txns > 0 else 0
    
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"\nCompanies tested: {len(results)}")
    print(f"Total transactions: {total_txns}")
    print(f"Auto-approved: {total_auto_approved} ({overall_rate:.1f}%)")
    print(f"Needs review: {total_txns - total_auto_approved} ({(total_txns - total_auto_approved)/total_txns*100:.1f}%)")
    
    # Engine stats
    stats = engine.get_stats()
    print(f"\nDecision Engine Statistics:")
    print(f"  Rules matches: {stats['rules_matches']} ({stats['rules_pct']:.1f}%)")
    print(f"  ML matches: {stats['ml_matches']} ({stats['ml_pct']:.1f}%)")
    print(f"  Manual review: {stats['manual_review']} ({stats['manual_pct']:.1f}%)")
    
    # Check target
    if overall_rate >= 80:
        print(f"\n✅ SUCCESS: {overall_rate:.1f}% automation rate (target: ≥80%)")
        return True
    else:
        print(f"\n⚠️  BELOW TARGET: {overall_rate:.1f}% automation rate (target: ≥80%)")
        return False


if __name__ == "__main__":
    success = test_ml_automation()
    sys.exit(0 if success else 1)

