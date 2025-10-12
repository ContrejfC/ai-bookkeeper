"""OFX bank statement parser."""
from typing import List
import hashlib
from datetime import datetime
from app.db.models import Transaction


def parse_ofx_statement(file_path: str) -> List[Transaction]:
    """
    Parse an OFX bank statement into normalized Transaction objects.
    
    Uses ofxparse library to read OFX files.
    
    Args:
        file_path: Path to the OFX file
        
    Returns:
        List of Transaction objects
    """
    try:
        import ofxparse
    except ImportError:
        raise ImportError("ofxparse library is required. Install with: pip install ofxparse")
    
    transactions = []
    
    with open(file_path, 'rb') as f:
        ofx = ofxparse.OfxParser.parse(f)
    
    # Process each account
    for account in ofx.accounts:
        for txn in account.statement.transactions:
            # Generate unique transaction ID
            txn_hash = hashlib.md5(
                f"{txn.date}{txn.payee}{txn.amount}".encode()
            ).hexdigest()[:16]
            
            # Normalize date
            date_str = txn.date.strftime("%Y-%m-%d") if txn.date else datetime.now().strftime("%Y-%m-%d")
            
            transaction = Transaction(
                txn_id=f"txn_{txn_hash}",
                date=date_str,
                amount=float(txn.amount),
                currency="USD",  # OFX doesn't always include currency
                description=txn.memo or txn.payee or "Unknown",
                counterparty=txn.payee or "Unknown",
                raw={
                    "id": txn.id,
                    "type": txn.type,
                    "checknum": txn.checknum,
                    "sic": txn.sic,
                },
                doc_ids=[]
            )
            
            transactions.append(transaction)
    
    return transactions

