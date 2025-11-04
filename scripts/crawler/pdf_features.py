"""
PII-Safe Feature Extraction
============================

Extract layout features from PDFs without storing full content or PII.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

logger = logging.getLogger(__name__)


def extract_safe_features(
    pdf_path: Path,
    max_pages: int = 3,
    pii_redaction: bool = True
) -> Dict[str, Any]:
    """
    Extract layout features from PDF without storing full content or PII.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to analyze (first N pages)
        pii_redaction: Enable PII redaction
        
    Returns:
        Dictionary of safe features (no PII, no full text)
    """
    if not HAS_PDFPLUMBER:
        raise ImportError("pdfplumber is required for feature extraction")
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    features = {
        "file_name": pdf_path.name,
        "file_hash": _compute_file_hash(pdf_path),
        "file_size_bytes": pdf_path.stat().st_size,
        "page_count": 0,
        "pages": []
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            features["page_count"] = len(pdf.pages)
            
            # Analyze first N pages only
            pages_to_analyze = min(max_pages, len(pdf.pages))
            
            for i in range(pages_to_analyze):
                page = pdf.pages[i]
                page_features = _extract_page_features(page, i + 1, pii_redaction)
                features["pages"].append(page_features)
    
    except Exception as e:
        logger.error(f"Error extracting features from {pdf_path}: {e}")
        features["error"] = str(e)
    
    return features


def _extract_page_features(page, page_num: int, pii_redaction: bool) -> Dict[str, Any]:
    """
    Extract features from a single page.
    
    Args:
        page: pdfplumber Page object
        page_num: Page number (1-indexed)
        pii_redaction: Enable PII redaction
        
    Returns:
        Dictionary of page features
    """
    page_height = page.height or 0
    page_width = page.width or 0
    
    # Extract text from different regions
    header_text = ""
    footer_text = ""
    
    if page_height > 0:
        # Header: top 20%
        header_region = page.within_bbox((0, 0, page_width, page_height * 0.20))
        header_text = (header_region.extract_text() or "").strip()
        
        # Footer: bottom 15%
        footer_region = page.within_bbox((0, page_height * 0.85, page_width, page_height))
        footer_text = (footer_region.extract_text() or "").strip()
    
    # Redact PII if enabled
    if pii_redaction:
        header_text = _redact_pii(header_text)
        footer_text = _redact_pii(footer_text)
    
    # Extract table information (structure only, not content)
    tables = page.extract_tables()
    table_info = []
    
    for table in tables:
        if table and len(table) > 0:
            # Get header row only (first row)
            header_row = table[0] if table else []
            clean_headers = [str(h).strip() if h else "" for h in header_row]
            
            # Redact PII from headers
            if pii_redaction:
                clean_headers = [_redact_pii(h) for h in clean_headers]
            
            table_info.append({
                "row_count": len(table),
                "column_count": len(header_row),
                "headers": clean_headers
            })
    
    # Compute geometry hints
    geometry = {
        "header_band": [0.0, 0.20],
        "table_band": [0.25, 0.80],
        "footer_band": [0.85, 1.0]
    }
    
    # Extract tokens (keywords) from header/footer
    header_tokens = _extract_tokens(header_text)
    footer_tokens = _extract_tokens(footer_text)
    
    return {
        "page_num": page_num,
        "page_width": round(page_width, 2),
        "page_height": round(page_height, 2),
        "header_tokens": header_tokens[:20],  # Limit to 20 tokens
        "footer_tokens": footer_tokens[:20],
        "table_count": len(tables),
        "tables": table_info,
        "geometry": geometry,
        "has_text": bool(header_text or footer_text)
    }


def _compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 hash as hex string
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def _redact_pii(text: str) -> str:
    """
    Redact common PII patterns from text.
    
    Args:
        text: Text to redact
        
    Returns:
        Redacted text
    """
    if not text:
        return text
    
    import re
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL***', text)
    
    # Phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '***PHONE***', text)
    text = re.sub(r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b', '***PHONE***', text)
    
    # SSN (9 digits with hyphens)
    text = re.sub(r'\b\d{3}[-]\d{2}[-]\d{4}\b', '***SSN***', text)
    
    # Account numbers (8-12 consecutive digits)
    text = re.sub(r'\b\d{8,12}\b', '***ACCOUNT***', text)
    
    # Credit card numbers (13-16 digits, may have spaces/hyphens)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{3,4}\b', '***CARD***', text)
    
    return text


def _extract_tokens(text: str) -> list:
    """
    Extract unique tokens (words) from text.
    
    Args:
        text: Text to tokenize
        
    Returns:
        List of unique tokens, lowercase, sorted
    """
    if not text:
        return []
    
    import re
    
    # Extract words (alphanumeric only)
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'
    }
    
    words = [w for w in words if w not in stop_words]
    
    # Return unique sorted
    return sorted(list(set(words)))


def save_features(features: Dict[str, Any], output_path: Path):
    """
    Save features to JSON file.
    
    Args:
        features: Features dictionary
        output_path: Path to save JSON
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(features, f, indent=2)
    
    logger.info(f"Saved features to {output_path}")


# Example usage
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_features.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        sys.exit(1)
    
    print(f"\nExtracting features from: {pdf_path}")
    
    features = extract_safe_features(pdf_path, max_pages=3, pii_redaction=True)
    
    print(f"\n{'='*80}")
    print("EXTRACTED FEATURES")
    print(f"{'='*80}\n")
    
    print(f"File: {features['file_name']}")
    print(f"Hash: {features['file_hash'][:16]}...")
    print(f"Size: {features['file_size_bytes']} bytes")
    print(f"Pages: {features['page_count']} (analyzed: {len(features.get('pages', []))})")
    
    for page in features.get('pages', []):
        print(f"\nPage {page['page_num']}:")
        print(f"  Size: {page['page_width']} x {page['page_height']}")
        print(f"  Tables: {page['table_count']}")
        print(f"  Header tokens: {', '.join(page['header_tokens'][:5])}")
        
        if page['tables']:
            for i, table in enumerate(page['tables'][:2]):
                print(f"  Table {i+1}: {table['row_count']} rows, {table['column_count']} cols")
                print(f"    Headers: {table['headers']}")
    
    # Save to temp file
    output_path = Path("out/temp_features.json")
    save_features(features, output_path)
    print(f"\nSaved to: {output_path}")



