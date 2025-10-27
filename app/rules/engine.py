"""
Rules Engine - Pattern-Based Transaction Categorization
=======================================================

This module provides deterministic, rule-based categorization of transactions
before falling back to AI/LLM categorization. Rules are faster, cheaper, and
more consistent than AI for known patterns.

Architecture:
------------
The rules engine is the first tier in the decision hierarchy:

1. Rules Engine (this file) - Fast, deterministic pattern matching
2. Embeddings/Vector Search - Historical transaction similarity
3. LLM Categorization - AI-powered fallback for novel transactions
4. Human Review - Low confidence or high-value transactions

Rules File:
----------
Rules are defined in YAML format (vendor_rules.yaml):

```yaml
rules:
  - pattern: "amazon\.com|amzn"
    account: "6100 Office Supplies"
    category: "office_supplies"
    
  - pattern: "uber|lyft"
    account: "6500 Travel & Transport"
    category: "transportation"
    match_condition: "amount < 0"  # Only expenses
    
default:
  positive_amount: "8000 Sales Revenue"
  negative_amount: "6999 Miscellaneous Expense"
```

Rule Structure:
--------------
- pattern: Regex pattern to match against description/counterparty
- account: Chart of accounts code (e.g., "6100 Office Supplies")
- category: Category slug for reporting
- match_condition: Optional Python expression for additional filtering
- confidence: Automatically set to 1.0 for rule matches

Matching Logic:
--------------
1. Iterate through all rules in order
2. Check if pattern matches transaction description or counterparty
3. If match_condition is present, evaluate it
4. Return first matching rule with account and rationale
5. If no rules match, return default based on transaction sign

Pattern Examples:
----------------
- Simple text: "walmart"
- Multiple options: "starbucks|sbux"
- Domain matching: "\.google\.com"
- Case insensitive: All patterns matched with re.IGNORECASE

Match Conditions:
----------------
Conditions can reference transaction fields:
- amount > 0 (revenue)
- amount < -100 (large expenses)
- "software" in description
- counterparty == "SPECIFIC VENDOR"

Performance:
-----------
Rules are loaded once at startup and cached in memory.
Pattern matching is O(n) where n = number of rules.
Typical performance: <1ms per transaction.

Rule Management:
---------------
- Rules can be version-controlled in database (RuleVersionDB)
- Adaptive rules can be promoted from evidence (RuleCandidateDB)
- Rules can be A/B tested before promotion
- Rule performance tracked in DecisionAuditLogDB

Usage Example:
-------------
```python
engine = RulesEngine()
result = engine.match_transaction(transaction)

if result['matched'] and result['confidence'] >= 0.9:
    # High confidence rule match, auto-post
    create_journal_entry(transaction, result)
else:
    # Fall back to LLM categorization
    llm_result = llm_categorizer.categorize(transaction)
```
"""
import re
import yaml
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.db.models import Transaction


class RulesEngine:
    """Rules-based transaction categorization engine."""
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the rules engine.
        
        Args:
            rules_file: Path to YAML rules file. If None, uses default location.
        """
        if rules_file is None:
            rules_file = Path(__file__).parent / "vendor_rules.yaml"
        
        self.rules = self._load_rules(rules_file)
    
    def _load_rules(self, rules_file: str) -> Dict[str, Any]:
        """Load rules from YAML file."""
        with open(rules_file, 'r') as f:
            return yaml.safe_load(f)
    
    def match_transaction(self, transaction: Transaction) -> Optional[Dict[str, Any]]:
        """
        Match a transaction against rules.
        
        Args:
            transaction: Transaction to match
            
        Returns:
            Dict with account, category, and rationale if matched, None otherwise
        """
        for rule in self.rules.get('rules', []):
            pattern = rule.get('pattern', '')
            
            # Check if pattern matches description or counterparty
            match_text = f"{transaction.description} {transaction.counterparty or ''}"
            
            if re.search(pattern, match_text, re.IGNORECASE):
                # Check additional match conditions if present
                match_condition = rule.get('match_condition', '')
                
                if match_condition:
                    if not self._evaluate_condition(match_condition, transaction):
                        continue
                
                return {
                    'account': rule['account'],
                    'category': rule.get('category', 'uncategorized'),
                    'rationale': f"Matched rule pattern: {pattern}",
                    'confidence': 1.0,
                    'matched': True
                }
        
        # No rule matched, use default
        default_rules = self.rules.get('default', {})
        
        if transaction.amount > 0:
            account = default_rules.get('positive_amount', '8000 Sales Revenue')
            rationale = "Default: positive amount (revenue)"
        else:
            account = default_rules.get('negative_amount', '6999 Miscellaneous Expense')
            rationale = "Default: negative amount (expense)"
        
        return {
            'account': account,
            'category': 'uncategorized',
            'rationale': rationale,
            'confidence': 0.5,
            'matched': False
        }
    
    def _evaluate_condition(self, condition: str, transaction: Transaction) -> bool:
        """
        Evaluate a match condition.
        
        Simple eval-based condition checking. Supports: amount, description, counterparty
        
        Args:
            condition: Condition string (e.g., "amount > 0")
            transaction: Transaction object
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Create a safe context with transaction attributes
            context = {
                'amount': transaction.amount,
                'description': transaction.description,
                'counterparty': transaction.counterparty,
            }
            
            # Replace attribute names in condition
            eval_condition = condition
            for key in context:
                eval_condition = eval_condition.replace(key, f"context['{key}']")
            
            return eval(eval_condition, {"context": context, "__builtins__": {}})
        except Exception:
            return True  # If evaluation fails, don't filter out
    
    def batch_match(self, transactions: List[Transaction]) -> Dict[str, Dict[str, Any]]:
        """
        Match multiple transactions at once.
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dict mapping txn_id to match results
        """
        results = {}
        
        for txn in transactions:
            results[txn.txn_id] = self.match_transaction(txn)
        
        return results

