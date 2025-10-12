"""PDF bank statement parser with OCR support."""
from typing import List
import re
from datetime import datetime
import hashlib
from app.db.models import Transaction
from app.ocr.extract_text import extract_text_from_pdf


def parse_pdf_statement(file_path: str) -> List[Transaction]:
    """
    Parse a PDF bank statement into normalized Transaction objects.
    
    Uses OCR to extract text, then applies regex patterns to find transactions.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        List of Transaction objects
    """
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    # Parse transactions from text
    transactions = parse_transactions_from_text(text)
    
    return transactions


def parse_transactions_from_text(text: str) -> List[Transaction]:
    """
    Extract transaction data from raw text using regex patterns.
    
    Looks for common patterns:
    - Date Amount Description
    - MM/DD/YYYY $XXX.XX Description
    
    Args:
        text: Raw text from PDF
        
    Returns:
        List of Transaction objects
    """
    transactions = []
    
    # Common pattern: date amount description
    # Example: "10/01/2025 -125.37 AMAZON MARKETPLACE"
    pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+([+-]?\$?[\d,]+\.\d{2})\s+(.+?)(?=\n|$)'
    
    matches = re.finditer(pattern, text, re.MULTILINE)
    
    for idx, match in enumerate(matches):
        date_str, amount_str, description = match.groups()
        
        # Parse date
        try:
            for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y-%m-%d"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    normalized_date = parsed_date.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            else:
                continue
        except Exception:
            continue
        
        # Parse amount
        amount_str = amount_str.replace('$', '').replace(',', '').strip()
        try:
            amount = float(amount_str)
        except ValueError:
            continue
        
        # Generate transaction ID
        txn_hash = hashlib.md5(
            f"{normalized_date}{description}{amount}{idx}".encode()
        ).hexdigest()[:16]
        
        transaction = Transaction(
            txn_id=f"txn_{txn_hash}",
            date=normalized_date,
            amount=amount,
            currency="USD",
            description=description.strip(),
            counterparty=description.strip().split()[0] if description.strip() else "Unknown",
            raw={"source": "pdf_ocr", "original_date": date_str},
            doc_ids=[file_path]
        )
        
        transactions.append(transaction)
    
    return transactions

