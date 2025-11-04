"""
CAMT Parser (ISO 20022)
=======================

Parses camt.053 (Bank to Customer Statement) and camt.054 (Debit/Credit Notification).

Standards: ISO 20022 XML schemas
Formats: camt.053.001.02, camt.053.001.08, camt.054.001.02, camt.054.001.08
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.ingestion.schemas import CanonicalTransaction


# Common ISO 20022 namespaces
NAMESPACES = {
    '053_02': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.02',
    '053_08': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.08',
    '054_02': 'urn:iso:std:iso:20022:tech:xsd:camt.054.001.02',
    '054_08': 'urn:iso:std:iso:20022:tech:xsd:camt.054.001.08',
}


def parse_camt(file_path: Path) -> List[CanonicalTransaction]:
    """
    Parse CAMT.053/054 XML to canonical transactions.
    
    Args:
        file_path: Path to CAMT XML file
        
    Returns:
        List of CanonicalTransaction objects
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Detect namespace
    namespace = _detect_namespace(root)
    ns = {'ns': namespace} if namespace else {}
    
    transactions = []
    
    # Find all entry records (Ntry elements)
    for entry in root.findall('.//ns:Ntry', ns) if ns else root.findall('.//Ntry'):
        try:
            txn = _parse_entry(entry, ns)
            if txn:
                transactions.append(txn)
        except Exception as e:
            # Log but continue processing other entries
            print(f"Warning: Failed to parse entry: {e}")
            continue
    
    return transactions


def _detect_namespace(root: ET.Element) -> Optional[str]:
    """Detect ISO 20022 namespace from root element."""
    tag = root.tag
    if '}' in tag:
        return tag.split('}')[0][1:]  # Extract namespace from {namespace}tag
    return None


def _parse_entry(entry: ET.Element, ns: Dict[str, str]) -> Optional[CanonicalTransaction]:
    """Parse a single Ntry (entry) element."""
    
    # Amount
    amt_elem = entry.find('ns:Amt', ns) if ns else entry.find('Amt')
    if amt_elem is None:
        return None
    
    amount = Decimal(amt_elem.text)
    currency = amt_elem.get('Ccy', 'USD')
    
    # Credit/Debit indicator
    cdt_dbt_ind = entry.find('ns:CdtDbtInd', ns) if ns else entry.find('CdtDbtInd')
    is_credit = cdt_dbt_ind is not None and cdt_dbt_ind.text == 'CRDT'
    
    # Apply sign (credit = positive, debit = negative)
    if not is_credit:
        amount = -amount
    
    # Booking date
    booking_date_elem = entry.find('ns:BookgDt/ns:Dt', ns) if ns else entry.find('BookgDt/Dt')
    value_date_elem = entry.find('ns:ValDt/ns:Dt', ns) if ns else entry.find('ValDt/Dt')
    
    date_str = None
    if booking_date_elem is not None:
        date_str = booking_date_elem.text
    elif value_date_elem is not None:
        date_str = value_date_elem.text
    
    post_date = datetime.fromisoformat(date_str).date() if date_str else None
    
    # Description from additional info or related parties
    description = _extract_description(entry, ns)
    
    # Reference
    acct_svcr_ref = entry.find('ns:AcctSvcrRef', ns) if ns else entry.find('AcctSvcrRef')
    reference = acct_svcr_ref.text if acct_svcr_ref is not None else None
    
    return CanonicalTransaction(
        post_date=post_date,
        description=description or "CAMT Entry",
        amount=float(amount),
        currency=currency,
        reference=reference,
        metadata={
            "source_format": "camt",
            "credit_debit_indicator": "CRDT" if is_credit else "DBIT"
        }
    )


def _extract_description(entry: ET.Element, ns: Dict[str, str]) -> str:
    """Extract description from entry details."""
    descriptions = []
    
    # Additional entry information
    addtl_info = entry.find('ns:AddtlNtryInf', ns) if ns else entry.find('AddtlNtryInf')
    if addtl_info is not None and addtl_info.text:
        descriptions.append(addtl_info.text)
    
    # Related parties
    for party_path in ['ns:NtryDtls/ns:TxDtls/ns:RltdPties/ns:Dbtr/ns:Nm',
                       'ns:NtryDtls/ns:TxDtls/ns:RltdPties/ns:Cdtr/ns:Nm']:
        if ns:
            party = entry.find(party_path, ns)
        else:
            party = entry.find(party_path.replace('ns:', ''))
        if party is not None and party.text:
            descriptions.append(party.text)
    
    # Remittance information
    rmtinf_path = 'ns:NtryDtls/ns:TxDtls/ns:RmtInf/ns:Ustrd' if ns else 'NtryDtls/TxDtls/RmtInf/Ustrd'
    rmtinf = entry.find(rmtinf_path, ns) if ns else entry.find(rmtinf_path)
    if rmtinf is not None and rmtinf.text:
        descriptions.append(rmtinf.text)
    
    return ' - '.join(descriptions) if descriptions else "Transaction"


# Example usage for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_camt(Path(sys.argv[1]))
        print(f"Parsed {len(result)} transactions")
        for txn in result[:5]:
            print(f"  {txn.post_date}: {txn.description} {txn.amount} {txn.currency}")



