"""
MT940 Parser (SWIFT)
====================

Parses SWIFT MT940 bank statement format.

Format: Tagged fields with :XX: prefixes
Key tags:
  :20: Transaction reference
  :25: Account number
  :28: Statement number
  :60F: Opening balance
  :61: Statement line (transaction)
  :62F: Closing balance
  :86: Additional information
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple
import re

from app.ingestion.schemas import CanonicalTransaction


def parse_mt940(file_path: Path) -> List[CanonicalTransaction]:
    """
    Parse MT940 file to canonical transactions.
    
    Args:
        file_path: Path to MT940 text file
        
    Returns:
        List of CanonicalTransaction objects
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    transactions = []
    
    # Split into records (each record starts with :20:)
    records = re.split(r'(?=:20:)', content)
    
    for record in records:
        if not record.strip():
            continue
        
        txns = _parse_record(record)
        transactions.extend(txns)
    
    return transactions


def _parse_record(record: str) -> List[CanonicalTransaction]:
    """Parse a single MT940 record."""
    transactions = []
    
    # Extract tags
    tags = _extract_tags(record)
    
    # Opening balance (for reference, not a transaction)
    opening_balance = _parse_balance_tag(tags.get('60F', ''))
    currency = opening_balance[1] if opening_balance else 'USD'
    
    # Parse each :61: tag (statement line)
    for tag_61 in tags.get_all('61'):
        try:
            txn = _parse_statement_line(tag_61, currency, tags)
            if txn:
                transactions.append(txn)
        except Exception as e:
            print(f"Warning: Failed to parse :61: line: {e}")
            continue
    
    return transactions


class TagDict:
    """Dict-like container that supports multiple values per key."""
    def __init__(self):
        self.data = {}
    
    def add(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
    
    def get(self, key: str, default='') -> str:
        values = self.data.get(key, [])
        return values[0] if values else default
    
    def get_all(self, key: str) -> List[str]:
        return self.data.get(key, [])


def _extract_tags(record: str) -> TagDict:
    """Extract all :XX: tags from record."""
    tags = TagDict()
    
    # Pattern: :TAG:VALUE (may span multiple lines until next tag)
    pattern = r':(\d{2,3}):((?:(?!:\d{2,3}:).)+)'
    
    for match in re.finditer(pattern, record, re.DOTALL):
        tag = match.group(1)
        value = match.group(2).strip()
        tags.add(tag, value)
    
    return tags


def _parse_statement_line(line_61: str, currency: str, tags: TagDict) -> Optional[CanonicalTransaction]:
    """
    Parse :61: statement line.
    
    Format: YYMMDD[MMDD]C/D[amount]N[type][//reference]
    Example: 231201C1000,00NTRFNONREF//PO12345
    """
    # Simplified parser for most common format
    # Real implementation would handle all SWIFT variants
    
    # Date (YYMMDD)
    date_match = re.match(r'(\d{6})', line_61)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    year = int('20' + date_str[0:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    post_date = datetime(year, month, day).date()
    
    # Credit/Debit indicator and amount
    cd_match = re.search(r'([CD])([\d,\.]+)', line_61[6:])
    if not cd_match:
        return None
    
    is_credit = cd_match.group(1) == 'C'
    amount_str = cd_match.group(2).replace(',', '.')
    amount = Decimal(amount_str)
    
    if not is_credit:
        amount = -amount
    
    # Reference
    ref_match = re.search(r'//(.+)', line_61)
    reference = ref_match.group(1) if ref_match else None
    
    # Try to get description from following :86: tag
    description = "MT940 Transaction"
    tag_86_list = tags.get_all('86')
    if tag_86_list:
        # Simple heuristic: use first :86: after this :61:
        description = tag_86_list[0][:100]  # Truncate long descriptions
    
    return CanonicalTransaction(
        post_date=post_date,
        description=description,
        amount=float(amount),
        currency=currency,
        reference=reference,
        metadata={
            "source_format": "mt940",
            "credit_debit": "C" if is_credit else "D"
        }
    )


def _parse_balance_tag(tag_60: str) -> Optional[Tuple[Decimal, str, datetime]]:
    """
    Parse :60F: opening balance.
    
    Format: C/DYYMMDDCCCAMOUNT
    Example: C231201USD100000,00
    """
    if len(tag_60) < 15:
        return None
    
    is_credit = tag_60[0] == 'C'
    date_str = tag_60[1:7]
    currency = tag_60[7:10]
    amount_str = tag_60[10:].replace(',', '.')
    
    try:
        amount = Decimal(amount_str)
        if not is_credit:
            amount = -amount
        
        year = int('20' + date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        date = datetime(year, month, day)
        
        return (amount, currency, date)
    except:
        return None


# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_mt940(Path(sys.argv[1]))
        print(f"Parsed {len(result)} transactions")
        for txn in result[:5]:
            print(f"  {txn.post_date}: {txn.description} {txn.amount} {txn.currency}")



