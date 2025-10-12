"""CSV bank statement parser."""
import csv
from datetime import datetime
from typing import List, Dict, Any
import uuid
from app.db.models import Transaction


def parse_csv_statement(file_path: str, date_format: str = "%Y-%m-%d") -> List[Transaction]:
    """
    Parse a CSV bank statement into normalized Transaction objects.
    
    Expected CSV columns: date, description, amount, [optional: counterparty, currency]
    
    Args:
        file_path: Path to the CSV file
        date_format: Date format string for parsing dates
        
    Returns:
        List of Transaction objects
    """
    transactions = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            # Generate a unique transaction ID using UUID4
            txn_id = uuid.uuid4().hex
            
            # Parse date
            date_str = row.get('date', '')
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                normalized_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                # Try alternative formats
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        normalized_date = parsed_date.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                else:
                    # Skip invalid dates
                    continue
            
            # Parse amount (handle negative signs and currency symbols)
            amount_str = row.get('amount', '0').replace('$', '').replace(',', '').strip()
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0.0
            
            # Extract counterparty (look for common patterns)
            description = row.get('description', '')
            counterparty = row.get('counterparty', extract_counterparty(description))
            
            transaction = Transaction(
                txn_id=f"txn_{txn_id}",
                date=normalized_date,
                amount=amount,
                currency=row.get('currency', 'USD'),
                description=description,
                counterparty=counterparty,
                raw=dict(row),
                doc_ids=[]
            )
            
            transactions.append(transaction)
    
    return transactions


def extract_counterparty(description: str) -> str:
    """
    Extract counterparty name from transaction description.
    
    Simple heuristics:
    - Take first few words
    - Remove common prefixes (DEBIT, CREDIT, POS, etc.)
    
    Args:
        description: Transaction description
        
    Returns:
        Extracted counterparty name
    """
    if not description:
        return "Unknown"
    
    # Remove common prefixes
    prefixes = ["DEBIT", "CREDIT", "POS", "ACH", "CHECK", "ATM", "WIRE", "TRANSFER"]
    words = description.split()
    
    filtered_words = []
    for word in words:
        if word.upper() not in prefixes and not word.startswith('#'):
            filtered_words.append(word)
    
    # Take first 1-3 words as counterparty
    counterparty = " ".join(filtered_words[:3]) if filtered_words else "Unknown"
    
    return counterparty.strip()

