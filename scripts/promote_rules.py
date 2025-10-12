#!/usr/bin/env python3
"""
Auto-promote high-performing counterparty→account mappings to rules.

Analyzes approved journal entries and creates rules for patterns with:
- ≥95% precision (consistent account selection)
- ≥20 occurrences (sufficient support)
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_db_context
from app.db.models import JournalEntryDB, TransactionDB


def analyze_patterns(lookback_days: int = 90, min_support: int = 20, min_precision: float = 0.95):
    """
    Analyze approved transactions for promotable patterns.
    
    Args:
        lookback_days: Days to look back
        min_support: Minimum occurrences required
        min_precision: Minimum precision required (0-1)
        
    Returns:
        List of promotable rules
    """
    print(f"\n📊 Analyzing patterns (last {lookback_days} days)...")
    
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    # Collect counterparty → account mappings
    patterns = defaultdict(list)
    
    with get_db_context() as db:
        # Get all approved/posted journal entries
        entries = db.query(JournalEntryDB, TransactionDB).join(
            TransactionDB,
            JournalEntryDB.source_txn_id == TransactionDB.txn_id
        ).filter(
            JournalEntryDB.status.in_(['approved', 'posted']),
            JournalEntryDB.created_at >= cutoff_date
        ).all()
        
        print(f"   Found {len(entries)} approved entries")
        
        for je, txn in entries:
            # Extract the non-cash account
            for line in je.lines:
                account = line.get('account', '')
                if 'Cash at Bank' not in account and account:
                    counterparty = txn.counterparty or txn.description[:30]
                    patterns[counterparty].append(account)
                    break
    
    # Analyze each pattern
    promotable = []
    
    for counterparty, accounts in patterns.items():
        support = len(accounts)
        
        if support < min_support:
            continue
        
        # Calculate precision (most common account / total)
        account_counts = Counter(accounts)
        most_common_account, most_common_count = account_counts.most_common(1)[0]
        precision = most_common_count / support
        
        if precision >= min_precision:
            promotable.append({
                'counterparty': counterparty,
                'account': most_common_account,
                'support': support,
                'precision': precision,
                'confidence': precision  # Use precision as confidence
            })
    
    # Sort by support
    promotable.sort(key=lambda x: x['support'], reverse=True)
    
    print(f"   Promotable patterns: {len(promotable)}")
    
    return promotable


def update_rules_file(promotable: list):
    """
    Update vendor_rules.yaml with new rules.
    
    Args:
        promotable: List of promotable rules
    """
    rules_file = Path(__file__).parent.parent / "app" / "rules" / "vendor_rules.yaml"
    
    # Load existing rules
    if rules_file.exists():
        with open(rules_file, 'r') as f:
            existing_rules = yaml.safe_load(f) or {'rules': []}
    else:
        existing_rules = {'rules': []}
    
    # Get existing counterparties
    existing_counterparties = {
        rule.get('counterparty', '').lower()
        for rule in existing_rules.get('rules', [])
    }
    
    # Add new rules
    added = 0
    for pattern in promotable:
        counterparty_lower = pattern['counterparty'].lower()
        
        if counterparty_lower not in existing_counterparties:
            new_rule = {
                'name': f"Auto-promoted: {pattern['counterparty']}",
                'counterparty': pattern['counterparty'],
                'account': pattern['account'],
                'confidence': float(pattern['confidence']),
                'auto_promoted': True,
                'promoted_at': datetime.now().isoformat(),
                'support': pattern['support'],
                'precision': float(pattern['precision'])
            }
            
            existing_rules['rules'].append(new_rule)
            existing_counterparties.add(counterparty_lower)
            added += 1
    
    if added > 0:
        # Write back
        with open(rules_file, 'w') as f:
            yaml.dump(existing_rules, f, default_flow_style=False, sort_keys=False)
        
        print(f"\n✅ Added {added} new rules to {rules_file}")
    else:
        print(f"\n   No new rules to add")


def main():
    """Main rule promotion pipeline."""
    print("\n" + "="*70)
    print("  AUTO-RULE PROMOTION")
    print("="*70)
    
    # Analyze patterns
    promotable = analyze_patterns(
        lookback_days=90,
        min_support=20,
        min_precision=0.95
    )
    
    if not promotable:
        print("\n   No patterns meet promotion criteria")
        return
    
    # Show top promotable patterns
    print(f"\n📋 Top {min(10, len(promotable))} promotable patterns:\n")
    print(f"{'Counterparty':<40} {'Account':<30} {'Support':<10} {'Precision'}")
    print("-" * 100)
    
    for pattern in promotable[:10]:
        print(f"{pattern['counterparty']:<40} {pattern['account']:<30} {pattern['support']:<10} {pattern['precision']:.1%}")
    
    # Update rules file
    update_rules_file(promotable)
    
    print("\n✅ Rule promotion complete!")


if __name__ == "__main__":
    main()

