"""Rules engine for automated transaction categorization."""
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

