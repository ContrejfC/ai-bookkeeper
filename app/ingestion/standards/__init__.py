"""
Standards-based Financial Format Parsers
========================================

Parsers for international banking standards:
- CAMT (ISO 20022): camt.053 (statement), camt.054 (notification)
- MT940 (SWIFT): Tagged transaction format
- BAI2: Cash Management Balancing format (US banks)
- OFX: Open Financial Exchange (SGML/XML)

All parsers return List[CanonicalTransaction] for uniform processing.
"""

from app.ingestion.standards.camt_parser import parse_camt
from app.ingestion.standards.mt940_parser import parse_mt940
from app.ingestion.standards.bai2_parser import parse_bai2
from app.ingestion.standards.ofx_parser import parse_ofx

__all__ = [
    "parse_camt",
    "parse_mt940",
    "parse_bai2",
    "parse_ofx",
]



