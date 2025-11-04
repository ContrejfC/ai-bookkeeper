"""
Transaction Reconciliation and Guards
=====================================

Validate transaction data integrity with balance checks, date sequences,
period consistency, and totals sanity checks.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional

from app.ingestion.config import config
from app.ingestion.schemas import CanonicalTransaction, ReconciliationResult

logger = logging.getLogger(__name__)


def reconcile_transactions(
    transactions: List[CanonicalTransaction],
    strict: bool = True
) -> ReconciliationResult:
    """
    Run all reconciliation checks on a batch of transactions.
    
    Args:
        transactions: List of canonical transactions
        strict: If True, any failure marks overall as failed
    
    Returns:
        ReconciliationResult with pass/fail and details
    """
    if not transactions:
        return ReconciliationResult(
            passed=True,
            checks=[],
            errors=[],
            warnings=["No transactions to reconcile"]
        )
    
    checks = []
    errors = []
    warnings = []
    
    # Run individual checks
    balance_pass, balance_details = check_running_balance(transactions)
    checks.append({
        "name": "running_balance",
        "passed": balance_pass,
        "details": balance_details
    })
    if not balance_pass:
        errors.extend(balance_details.get('errors', []))
    
    date_pass, date_details = check_date_sequence(transactions)
    checks.append({
        "name": "date_sequence",
        "passed": date_pass,
        "details": date_details
    })
    if not date_pass:
        warnings.extend(date_details.get('warnings', []))
    
    period_pass, period_details = check_period_consistency(transactions)
    checks.append({
        "name": "period_consistency",
        "passed": period_pass,
        "details": period_details
    })
    if not period_pass:
        warnings.extend(period_details.get('warnings', []))
    
    totals_pass, totals_details = check_totals_sanity(transactions)
    checks.append({
        "name": "totals_sanity",
        "passed": totals_pass,
        "details": totals_details
    })
    if not totals_pass:
        warnings.extend(totals_details.get('warnings', []))
    
    # Check for multi-account splits
    split_detected, split_details = detect_multi_account(transactions)
    if split_detected:
        warnings.append(f"Multiple accounts detected: {split_details['accounts']}")
    
    # Overall pass/fail
    if strict:
        passed = all(c['passed'] for c in checks)
    else:
        # Only fail on critical errors (balance issues)
        passed = balance_pass
    
    return ReconciliationResult(
        passed=passed,
        checks=checks,
        errors=errors,
        warnings=warnings,
        balance_check=balance_pass,
        date_sequence_check=date_pass,
        period_consistency_check=period_pass,
        totals_sanity_check=totals_pass
    )


def check_running_balance(
    transactions: List[CanonicalTransaction],
    tolerance: float = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify running balance calculations.
    
    Checks that each transaction's balance equals the previous balance
    plus the transaction amount (within tolerance).
    
    Args:
        transactions: List of transactions (should be date-ordered)
        tolerance: Balance tolerance in currency units (default from config)
    
    Returns:
        Tuple of (passed, details_dict)
    """
    if tolerance is None:
        tolerance = config.BALANCE_TOLERANCE
    
    # Filter transactions that have balance information
    with_balance = [t for t in transactions if t.balance is not None]
    
    if not with_balance:
        return True, {
            "message": "No balance information to validate",
            "validated_count": 0
        }
    
    # Sort by post_date
    sorted_txns = sorted(with_balance, key=lambda t: t.post_date)
    
    errors = []
    validated = 0
    
    for i in range(1, len(sorted_txns)):
        prev = sorted_txns[i - 1]
        curr = sorted_txns[i]
        
        # Calculate expected balance
        expected_balance = float(prev.balance) + float(curr.amount)
        actual_balance = float(curr.balance)
        
        # Check if within tolerance
        difference = abs(expected_balance - actual_balance)
        
        if difference > tolerance:
            errors.append(
                f"Balance mismatch on {curr.post_date}: "
                f"expected {expected_balance:.2f}, got {actual_balance:.2f} "
                f"(diff: {difference:.2f})"
            )
        else:
            validated += 1
    
    passed = len(errors) == 0
    
    return passed, {
        "validated_count": validated,
        "total_with_balance": len(with_balance),
        "errors": errors,
        "tolerance": tolerance
    }


def check_date_sequence(
    transactions: List[CanonicalTransaction]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check that transaction dates are in reasonable sequence.
    
    Warnings for:
    - Dates not monotonically increasing
    - Large gaps between transactions
    - Future dates
    
    Args:
        transactions: List of transactions
    
    Returns:
        Tuple of (passed, details_dict)
    """
    if len(transactions) < 2:
        return True, {"message": "Not enough transactions for sequence check"}
    
    sorted_txns = sorted(transactions, key=lambda t: t.post_date)
    
    warnings = []
    today = date.today()
    
    # Check for future dates
    future_dates = [t for t in sorted_txns if t.post_date > today]
    if future_dates:
        warnings.append(
            f"{len(future_dates)} transaction(s) with future dates"
        )
    
    # Check for non-monotonic dates (if pre-sorted)
    non_monotonic = 0
    for i in range(1, len(sorted_txns)):
        if sorted_txns[i].post_date < sorted_txns[i-1].post_date:
            non_monotonic += 1
    
    if non_monotonic > 0:
        warnings.append(f"{non_monotonic} out-of-sequence date(s)")
    
    # Check for large gaps
    max_gap_days = 90  # 90 days
    large_gaps = []
    
    for i in range(1, len(sorted_txns)):
        gap = (sorted_txns[i].post_date - sorted_txns[i-1].post_date).days
        if gap > max_gap_days:
            large_gaps.append({
                "from": str(sorted_txns[i-1].post_date),
                "to": str(sorted_txns[i].post_date),
                "gap_days": gap
            })
    
    if large_gaps:
        warnings.append(f"{len(large_gaps)} gap(s) over {max_gap_days} days")
    
    # Check for very old dates (>10 years)
    ten_years_ago = today - timedelta(days=365*10)
    very_old = [t for t in sorted_txns if t.post_date < ten_years_ago]
    if very_old:
        warnings.append(f"{len(very_old)} transaction(s) older than 10 years")
    
    # Pass if no critical issues (future dates are warnings, not failures)
    passed = len(warnings) == 0 or all('future' not in w for w in warnings)
    
    return passed, {
        "warnings": warnings,
        "date_range": {
            "earliest": str(sorted_txns[0].post_date),
            "latest": str(sorted_txns[-1].post_date)
        },
        "large_gaps": large_gaps[:5]  # Report first 5 large gaps
    }


def check_period_consistency(
    transactions: List[CanonicalTransaction]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check that transactions span a consistent period.
    
    Args:
        transactions: List of transactions
    
    Returns:
        Tuple of (passed, details_dict)
    """
    if not transactions:
        return True, {"message": "No transactions"}
    
    sorted_txns = sorted(transactions, key=lambda t: t.post_date)
    
    earliest = sorted_txns[0].post_date
    latest = sorted_txns[-1].post_date
    span_days = (latest - earliest).days
    
    warnings = []
    
    # Check for very short periods with many transactions
    if span_days < 7 and len(transactions) > 100:
        warnings.append(
            f"Unusually high transaction density: "
            f"{len(transactions)} transactions in {span_days} days"
        )
    
    # Check for very long periods
    if span_days > 400:  # More than ~13 months
        warnings.append(
            f"Unusually long period: {span_days} days "
            f"({span_days / 30:.1f} months)"
        )
    
    # Check transaction distribution
    if span_days > 0:
        avg_per_day = len(transactions) / span_days
        if avg_per_day > 50:
            warnings.append(
                f"Very high transaction rate: {avg_per_day:.1f} per day"
            )
    
    passed = len(warnings) == 0
    
    return passed, {
        "span_days": span_days,
        "transaction_count": len(transactions),
        "warnings": warnings
    }


def check_totals_sanity(
    transactions: List[CanonicalTransaction]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check that transaction totals are reasonable.
    
    Args:
        transactions: List of transactions
    
    Returns:
        Tuple of (passed, details_dict)
    """
    if not transactions:
        return True, {"message": "No transactions"}
    
    warnings = []
    
    # Calculate totals
    total_debits = sum(float(t.amount) for t in transactions if float(t.amount) < 0)
    total_credits = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    net_change = total_debits + total_credits
    
    # Check if all transactions are one-sided (all debits or all credits)
    if total_debits == 0:
        warnings.append("No debit transactions (all positive amounts)")
    elif total_credits == 0:
        warnings.append("No credit transactions (all negative amounts)")
    
    # Check for extremely imbalanced ratios
    if total_credits != 0:
        debit_credit_ratio = abs(total_debits / total_credits)
        if debit_credit_ratio > 100 or debit_credit_ratio < 0.01:
            warnings.append(
                f"Highly imbalanced debit/credit ratio: {debit_credit_ratio:.2f}"
            )
    
    # Check for unreasonably large totals
    max_reasonable = 100_000_000  # $100M
    if abs(total_debits) > max_reasonable or abs(total_credits) > max_reasonable:
        warnings.append("Unusually large transaction totals")
    
    # Check average transaction size
    if transactions:
        avg_amount = abs(sum(float(t.amount) for t in transactions) / len(transactions))
        if avg_amount > 1_000_000:  # Average > $1M
            warnings.append(f"Very high average transaction: ${avg_amount:,.2f}")
        elif avg_amount < 0.01:  # Average < 1 cent
            warnings.append(f"Very low average transaction: ${avg_amount:.4f}")
    
    passed = len(warnings) == 0
    
    return passed, {
        "total_debits": total_debits,
        "total_credits": total_credits,
        "net_change": net_change,
        "transaction_count": len(transactions),
        "warnings": warnings
    }


def detect_multi_account(
    transactions: List[CanonicalTransaction]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if transactions span multiple accounts.
    
    Args:
        transactions: List of transactions
    
    Returns:
        Tuple of (has_multiple_accounts, details_dict)
    """
    if not transactions:
        return False, {}
    
    # Get unique accounts
    accounts = set(t.account_id for t in transactions if t.account_id)
    
    if len(accounts) <= 1:
        return False, {
            "account_count": len(accounts),
            "accounts": list(accounts)
        }
    
    # Count transactions per account
    account_counts = {}
    for txn in transactions:
        if txn.account_id:
            account_counts[txn.account_id] = account_counts.get(txn.account_id, 0) + 1
    
    return True, {
        "account_count": len(accounts),
        "accounts": list(accounts),
        "distribution": account_counts
    }


def validate_currency_consistency(
    transactions: List[CanonicalTransaction]
) -> Tuple[bool, List[str]]:
    """
    Check that all transactions use the same currency.
    
    Args:
        transactions: List of transactions
    
    Returns:
        Tuple of (is_consistent, currencies_found)
    """
    currencies = set(t.currency for t in transactions if t.currency)
    
    if len(currencies) <= 1:
        return True, list(currencies)
    
    logger.warning(f"Multiple currencies detected: {currencies}")
    return False, list(currencies)


def split_by_account(
    transactions: List[CanonicalTransaction]
) -> Dict[str, List[CanonicalTransaction]]:
    """
    Split transactions by account ID.
    
    Args:
        transactions: List of transactions
    
    Returns:
        Dictionary mapping account_id to list of transactions
    """
    accounts = {}
    
    for txn in transactions:
        account_id = txn.account_id or "unknown"
        if account_id not in accounts:
            accounts[account_id] = []
        accounts[account_id].append(txn)
    
    return accounts



