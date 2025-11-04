"""
Content Type Detection for Multi-Format Crawler
===============================================

Robust MIME type and format detection for PDF, CSV, XML, TXT files.
Handles mismatched extensions and Content-Type headers via magic bytes.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Magic bytes for common formats
MAGIC_BYTES = {
    "pdf": [
        b"%PDF-",  # PDF signature
    ],
    "csv": [
        # CSV doesn't have magic bytes, detect by content analysis
    ],
    "xml": [
        b"<?xml",  # XML declaration
        b"<",  # Generic XML/HTML start
    ],
    "txt": [
        # Plain text, no magic bytes
    ],
}

# MIME type mappings
MIME_TO_TYPE = {
    "application/pdf": "pdf",
    "application/x-pdf": "pdf",
    "text/csv": "csv",
    "application/csv": "csv",
    "text/comma-separated-values": "csv",
    "application/vnd.ms-excel": "csv",  # Sometimes used for CSV
    "application/xml": "xml",
    "text/xml": "xml",
    "application/x-xml": "xml",
    "text/plain": "txt",
    "application/octet-stream": None,  # Needs magic byte detection
}

# Extension mappings
EXT_TO_TYPE = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xml": "xml",
    ".txt": "txt",
    ".ofx": "xml",  # OFX is XML-based
    ".qfx": "xml",  # QFX is XML-based
    ".qbo": "xml",  # QBO is XML-based
    ".bai": "txt",  # BAI2 is text-based
    ".mt940": "txt",  # MT940 is text-based
    ".sta": "txt",  # Statement files often use .sta
}


def detect_content_type(
    file_content: bytes,
    content_type_header: Optional[str] = None,
    file_name: Optional[str] = None,
    url: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Detect file type using multiple strategies.
    
    Args:
        file_content: First bytes of the file (at least 4096 bytes recommended)
        content_type_header: HTTP Content-Type header if available
        file_name: Original file name if available
        url: URL of the file if available
        
    Returns:
        Tuple of (detected_type, confidence)
        detected_type: "pdf", "csv", "xml", "txt", or None
        confidence: "high", "medium", "low"
    """
    if not file_content:
        return None, "low"
    
    # Strategy 1: Check magic bytes (highest confidence)
    magic_type = _detect_by_magic_bytes(file_content)
    if magic_type:
        logger.debug(f"Detected {magic_type} by magic bytes")
        return magic_type, "high"
    
    # Strategy 2: Check Content-Type header
    if content_type_header:
        mime_type = _extract_mime_type(content_type_header)
        header_type = MIME_TO_TYPE.get(mime_type)
        if header_type:
            logger.debug(f"Detected {header_type} by Content-Type header: {mime_type}")
            return header_type, "medium"
    
    # Strategy 3: Check file extension
    ext_type = None
    if file_name:
        ext_type = _detect_by_extension(file_name)
    elif url:
        ext_type = _detect_by_extension(url)
    
    if ext_type:
        logger.debug(f"Detected {ext_type} by file extension")
        return ext_type, "low"
    
    # Strategy 4: Content analysis for CSV/TXT
    analysis_type = _detect_by_content_analysis(file_content)
    if analysis_type:
        logger.debug(f"Detected {analysis_type} by content analysis")
        return analysis_type, "medium"
    
    logger.warning(f"Could not detect file type for {file_name or url}")
    return None, "low"


def _detect_by_magic_bytes(content: bytes) -> Optional[str]:
    """Detect file type by magic bytes."""
    if len(content) < 5:
        return None
    
    # Check PDF
    if content.startswith(b"%PDF-"):
        return "pdf"
    
    # Check XML (flexible check)
    content_start = content[:100].strip()
    if content_start.startswith(b"<?xml") or content_start.startswith(b"<"):
        # Further check if it's actually XML vs HTML
        if b"<html" in content[:1000].lower() or b"<!doctype html" in content[:1000].lower():
            return None  # It's HTML, not a statement XML
        return "xml"
    
    return None


def _extract_mime_type(content_type: str) -> str:
    """Extract MIME type from Content-Type header (removes charset, etc.)."""
    return content_type.split(";")[0].strip().lower()


def _detect_by_extension(path: str) -> Optional[str]:
    """Detect file type by extension."""
    ext = Path(path).suffix.lower()
    return EXT_TO_TYPE.get(ext)


def _detect_by_content_analysis(content: bytes) -> Optional[str]:
    """
    Analyze content to detect CSV or specialized text formats.
    
    Checks for:
    - CSV: comma-separated values with consistent column counts
    - BAI2: Starts with "01," record
    - MT940: Starts with ":20:" or ":25:" tags
    - Plain text: printable ASCII/UTF-8
    """
    if len(content) < 10:
        return None
    
    try:
        text = content.decode('utf-8', errors='ignore')
        lines = text.split('\n')[:10]  # Check first 10 lines
        
        # Check for BAI2 format
        if lines and lines[0].strip().startswith("01,"):
            logger.debug("Detected BAI2 format")
            return "txt"
        
        # Check for MT940 format
        if any(line.strip().startswith(":20:") or line.strip().startswith(":25:") for line in lines):
            logger.debug("Detected MT940 format")
            return "txt"
        
        # Check for CSV (at least 2 lines with consistent comma counts)
        if len(lines) >= 2:
            comma_counts = [line.count(',') for line in lines if line.strip()]
            if comma_counts and len(set(comma_counts)) <= 2 and max(comma_counts) >= 2:
                logger.debug("Detected CSV format by comma analysis")
                return "csv"
        
        # Check for tab-separated (TSV treated as CSV)
        if len(lines) >= 2:
            tab_counts = [line.count('\t') for line in lines if line.strip()]
            if tab_counts and len(set(tab_counts)) <= 2 and max(tab_counts) >= 2:
                logger.debug("Detected TSV format (treated as CSV)")
                return "csv"
        
        # Default to txt if mostly printable
        if _is_mostly_printable(text[:1000]):
            return "txt"
    
    except Exception as e:
        logger.debug(f"Content analysis failed: {e}")
    
    return None


def _is_mostly_printable(text: str, threshold: float = 0.8) -> bool:
    """Check if text is mostly printable characters."""
    if not text:
        return False
    
    printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
    return (printable_count / len(text)) >= threshold


def is_statement_like(file_content: bytes, detected_type: str) -> bool:
    """
    Additional check to filter out non-statement files.
    
    Returns False for things like:
    - HTML pages
    - JavaScript
    - Images
    - Binary executables
    """
    if detected_type == "pdf":
        # PDF check: ensure it's not a brochure or form by checking size
        # Real statements are typically 20KB - 5MB
        if len(file_content) < 10000:  # < 10KB probably not a real statement
            logger.debug("PDF too small to be a statement")
            return False
    
    elif detected_type == "xml":
        # XML check: look for statement-related tags
        try:
            text = file_content[:5000].decode('utf-8', errors='ignore').lower()
            statement_indicators = [
                "statement", "transaction", "balance", "account",
                "ofx", "qfx", "camt", "document", "stmt"
            ]
            if not any(indicator in text for indicator in statement_indicators):
                logger.debug("XML doesn't appear to be statement-related")
                return False
        except:
            pass
    
    elif detected_type == "csv":
        # CSV check: look for transaction-like headers
        try:
            text = file_content[:1000].decode('utf-8', errors='ignore').lower()
            transaction_headers = [
                "date", "amount", "description", "balance", "debit", "credit",
                "transaction", "posting", "reference"
            ]
            if not any(header in text for header in transaction_headers):
                logger.debug("CSV doesn't appear to contain transaction data")
                return False
        except:
            pass
    
    return True


def get_file_size_limit(detected_type: str, config: dict) -> int:
    """Get size limit in bytes for a given file type."""
    size_limits = {
        "pdf": config.get("pdf_max_mb", 10) * 1024 * 1024,
        "csv": config.get("csv_max_mb", 5) * 1024 * 1024,
        "xml": config.get("xml_max_mb", 5) * 1024 * 1024,
        "txt": config.get("txt_max_mb", 2) * 1024 * 1024,
    }
    return size_limits.get(detected_type, 10 * 1024 * 1024)  # Default 10MB


# Example usage
if __name__ == "__main__":
    # Test detection
    test_cases = [
        (b"%PDF-1.4\n...", "application/pdf", "statement.pdf"),
        (b"Date,Description,Amount\n01/01/2023,Purchase,100.00", "text/csv", "transactions.csv"),
        (b"<?xml version='1.0'?><OFX>...", "application/xml", "statement.ofx"),
        (b"01,ACME Corp,123456...", "text/plain", "statement.bai"),
        (b":20:REFERENCE\n:25:ACCOUNT", "text/plain", "statement.mt940"),
    ]
    
    for content, mime, filename in test_cases:
        detected_type, confidence = detect_content_type(content, mime, filename)
        print(f"{filename}: {detected_type} ({confidence} confidence)")
        print(f"  Statement-like: {is_statement_like(content, detected_type)}")



