"""
BAI2 Parser - Cash Management Balancing
========================================

Parses BAI2 format used by US banks for account analysis.

Record Types:
  01 - File Header
  02 - Group Header
  03 - Account Identifier
  16 - Transaction Detail
  49 - Account Trailer
  98 - Group Trailer
  99 - File Trailer
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from app.ingestion.schemas import CanonicalTransaction


def parse_bai2(file_path: Path) -> List[CanonicalTransaction]:
    """
    Parse BAI2 format to canonical transactions.
    
    Args:
        file_path: Path to BAI2 text file
        
    Returns:
        List of CanonicalTransaction objects
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    transactions = []
    current_account = None
    current_currency = "USD"
    current_date = datetime.now().date()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        record_type = line[:2]
        
        if record_type == "02":  # Group Header
            # Extract date from position 12-17 (YYMMDD)
            parts = line.split(',')
            if len(parts) >= 4:
                date_str = parts[3]
                if len(date_str) == 6:
                    current_date = _parse_bai2_date(date_str)
        
        elif record_type == "03":  # Account Identifier
            # Format: 03,account_number,currency,type_code,...
            parts = line.split(',')
            if len(parts) >= 3:
                current_account = parts[1]
                currency_str = parts[2]
                current_currency = currency_str if len(currency_str) == 3 else "USD"
        
        elif record_type == "16":  # Transaction Detail
            txn = _parse_bai2_transaction(line, current_currency, current_account, current_date)
            if txn:
                transactions.append(txn)
    
    return transactions


def _parse_bai2_date(date_str: str) -> datetime.date:
    """Parse BAI2 date format (YYMMDD)."""
    if len(date_str) != 6:
        return datetime.now().date()
    
    year = int('20' + date_str[0:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    
    return datetime(year, month, day).date()


def _parse_bai2_transaction(line: str, currency: str, account: str, post_date: datetime.date) -> Optional[CanonicalTransaction]:
    """
    Parse 16 record (transaction detail).
    
    Format: 16,type_code,amount,funds_type,bank_ref,customer_ref,text/
    """
    parts = line.split(',')
    
    if len(parts) < 3:
        return None
    
    type_code = parts[1]
    amount_str = parts[2].replace(',', '')
    
    try:
        # BAI2 amounts are in cents (implied decimal)
        amount = Decimal(amount_str) / 100
    except (ValueError, InvalidOperation):
        return None
    
    # Type code determines credit/debit
    # 100-399: Debit, 400-699: Credit, 700-999: Varies
    type_code_int = int(type_code) if type_code.isdigit() else 0
    
    is_credit = False
    if 400 <= type_code_int < 700:
        is_credit = True
    elif type_code_int == 165:  # Specific debit code
        is_credit = False
    elif type_code_int == 475:  # Specific credit code
        is_credit = True
    
    if not is_credit:
        amount = -amount
    
    # Extract reference and description
    bank_ref = parts[3] if len(parts) > 3 and parts[3] else None
    customer_ref = parts[4] if len(parts) > 4 and parts[4] else None
    description = parts[5] if len(parts) > 5 and parts[5] else "BAI2 Transaction"
    
    # Remove trailing slash
    description = description.rstrip('/')
    
    # Use customer ref or bank ref as reference
    reference = customer_ref or bank_ref
    
    return CanonicalTransaction(
        post_date=post_date,
        description=description,
        amount=float(amount),
        currency=currency,
        reference=reference,
        metadata={
            "source_format": "bai2",
            "type_code": type_code,
            "account": account
        }
    )


# Example usage
if __name__ == "__main__":
    import sys
    from decimal import InvalidOperation
    if len(sys.argv) > 1:
        result = parse_bai2(Path(sys.argv[1]))
        print(f"Parsed {len(result)} transactions")
        for txn in result[:5]:
            print(f"  {txn.post_date}: {txn.description} {txn.amount} {txn.currency}")



