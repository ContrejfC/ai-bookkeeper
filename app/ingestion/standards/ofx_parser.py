"""
OFX Parser - Open Financial Exchange
====================================

Parses OFX format (both SGML and XML variants).

Format variants:
- OFX 1.x: SGML-like format with unclosed tags
- OFX 2.x: Proper XML format

Key elements:
- STMTTRN: Statement transaction
- FITID: Financial Institution Transaction ID
- DTPOSTED: Posting date
- TRNAMT: Transaction amount
- NAME: Payee name
- MEMO: Additional description
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from app.ingestion.schemas import CanonicalTransaction


def parse_ofx(file_path: Path) -> List[CanonicalTransaction]:
    """
    Parse OFX (SGML or XML variant) to canonical transactions.
    
    Args:
        file_path: Path to OFX file
        
    Returns:
        List of CanonicalTransaction objects
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Detect if XML or SGML
    is_xml = content.strip().startswith('<?xml')
    
    if not is_xml:
        # Convert SGML to XML
        content = _sgml_to_xml(content)
    
    # Parse XML
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        # Try wrapping in root element
        try:
            content = f"<OFX>{content}</OFX>"
            root = ET.fromstring(content)
        except ET.ParseError:
            print(f"Error parsing OFX: {e}")
            return []
    
    transactions = []
    
    # Find all STMTTRN (statement transaction) elements
    for stmttrn in root.findall('.//STMTTRN'):
        txn = _parse_stmttrn(stmttrn)
        if txn:
            transactions.append(txn)
    
    return transactions


def _sgml_to_xml(sgml_content: str) -> str:
    """
    Convert OFX SGML to XML by closing tags.
    
    OFX 1.x uses SGML syntax where tags don't need to be closed:
    <TAG>value
    
    Convert to XML:
    <TAG>value</TAG>
    """
    lines = []
    tag_stack = []
    
    for line in sgml_content.split('\n'):
        line = line.strip()
        
        if not line or line.startswith('<!--'):
            continue
        
        # Handle opening tags
        if line.startswith('<') and not line.startswith('</'):
            # Extract tag name
            tag_match = re.match(r'<([A-Z0-9_]+)>(.*)$', line)
            if tag_match:
                tag_name = tag_match.group(1)
                value = tag_match.group(2).strip()
                
                if value:
                    # Tag with value on same line
                    lines.append(f"<{tag_name}>{value}</{tag_name}>")
                else:
                    # Opening tag only
                    lines.append(f"<{tag_name}>")
                    tag_stack.append(tag_name)
            else:
                lines.append(line)
        
        # Handle closing tags
        elif line.startswith('</'):
            if tag_stack:
                tag_stack.pop()
            lines.append(line)
        
        else:
            # Content line
            lines.append(line)
    
    # Close any remaining open tags
    while tag_stack:
        tag_name = tag_stack.pop()
        lines.append(f"</{tag_name}>")
    
    return '\n'.join(lines)


def _parse_stmttrn(stmttrn: ET.Element) -> Optional[CanonicalTransaction]:
    """Parse STMTTRN (statement transaction) element."""
    
    # FITID (unique transaction ID)
    fitid = stmttrn.find('FITID')
    reference = fitid.text.strip() if fitid is not None and fitid.text else None
    
    # DTPOSTED (posting date) - format: YYYYMMDD or YYYYMMDDHHMMSS
    dtposted = stmttrn.find('DTPOSTED')
    if dtposted is None or not dtposted.text:
        return None
    
    date_str = dtposted.text.strip()[:8]  # Take YYYYMMDD
    try:
        post_date = datetime.strptime(date_str, '%Y%m%d').date()
    except ValueError:
        return None
    
    # TRNAMT (transaction amount)
    trnamt = stmttrn.find('TRNAMT')
    if trnamt is None or not trnamt.text:
        return None
    
    try:
        amount = Decimal(trnamt.text.strip())
    except (ValueError, InvalidOperation):
        return None
    
    # NAME and MEMO for description
    name = stmttrn.find('NAME')
    memo = stmttrn.find('MEMO')
    
    description_parts = []
    if name is not None and name.text:
        description_parts.append(name.text.strip())
    if memo is not None and memo.text:
        description_parts.append(memo.text.strip())
    
    description = ' - '.join(description_parts) if description_parts else "OFX Transaction"
    
    # Currency (search in parent elements or use default)
    currency = "USD"
    curdef = stmttrn.find('.//CURDEF')
    if curdef is not None and curdef.text:
        currency = curdef.text.strip()
    else:
        # Try finding in parent STMTRS
        parent = stmttrn
        for _ in range(5):  # Search up to 5 levels
            parent = list(stmttrn.iter())
            if parent:
                curdef = parent[0].find('.//CURDEF')
                if curdef is not None and curdef.text:
                    currency = curdef.text.strip()
                    break
    
    # TRNTYPE for additional context
    trntype = stmttrn.find('TRNTYPE')
    trntype_value = trntype.text.strip() if trntype is not None and trntype.text else None
    
    return CanonicalTransaction(
        post_date=post_date,
        description=description,
        amount=float(amount),
        currency=currency,
        reference=reference,
        metadata={
            "source_format": "ofx",
            "fitid": reference,
            "trntype": trntype_value
        }
    )


# Example usage
if __name__ == "__main__":
    import sys
    from decimal import InvalidOperation
    if len(sys.argv) > 1:
        result = parse_ofx(Path(sys.argv[1]))
        print(f"Parsed {len(result)} transactions")
        for txn in result[:5]:
            print(f"  {txn.post_date}: {txn.description} {txn.amount} {txn.currency}")



