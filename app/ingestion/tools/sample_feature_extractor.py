"""
Sample Feature Extractor
=========================

Extract non-PII features from bank statement PDFs for template building.

Features extracted:
- Header tokens (keywords, bank names, terms)
- Table structure (headers, column positions)
- Date format hints
- Geometry/layout bands
- Text density patterns

NO full text or PII is stored.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from app.ingestion.utils.pii import redact_pii

logger = logging.getLogger(__name__)


# Common bank statement keywords
BANK_KEYWORDS = [
    'statement', 'account', 'balance', 'transaction', 'deposit', 'withdrawal',
    'checking', 'savings', 'credit', 'debit', 'date', 'description', 'amount',
    'beginning', 'ending', 'total', 'summary', 'period', 'interest',
    'fee', 'charge', 'payment', 'transfer', 'pending', 'posted',
    'available', 'overdraft', 'minimum', 'maximum', 'average',
    'routing', 'branch', 'institution', 'customer', 'member',
]

# Date format patterns
DATE_PATTERNS = [
    (r'\d{2}/\d{2}/\d{4}', 'MM/DD/YYYY'),
    (r'\d{4}-\d{2}-\d{2}', 'YYYY-MM-DD'),
    (r'\d{2}-\d{2}-\d{4}', 'MM-DD-YYYY'),
    (r'\d{2}\.\d{2}\.\d{4}', 'MM.DD.YYYY'),
    (r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}', 'Mon DD, YYYY'),
    (r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', 'DD Mon YYYY'),
]

# Amount/currency patterns
AMOUNT_PATTERNS = [
    (r'\$\s*[\d,]+\.\d{2}', 'USD_DOLLAR_SIGN'),
    (r'[\d,]+\.\d{2}\s*USD', 'USD_SUFFIX'),
    (r'\([\d,]+\.\d{2}\)', 'PARENTHESES_NEGATIVE'),
    (r'[\d,]+\.\d{2}-', 'MINUS_SUFFIX'),
]


def extract_features(pdf_path: str, redact_pii: bool = True) -> Dict[str, Any]:
    """
    Extract features from a PDF bank statement.
    
    Args:
        pdf_path: Path to PDF file
        redact_pii: Whether to redact PII from features
    
    Returns:
        Dictionary of extracted features
    """
    if not HAS_PDFPLUMBER and not HAS_PYMUPDF:
        raise ImportError("Neither pdfplumber nor PyMuPDF is installed. Install one to extract features.")
    
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    logger.info(f"Extracting features from: {pdf_path.name}")
    
    # Use pdfplumber if available, else PyMuPDF
    if HAS_PDFPLUMBER:
        features = _extract_with_pdfplumber(pdf_path)
    else:
        features = _extract_with_pymupdf(pdf_path)
    
    # Redact PII if requested
    if redact_pii:
        features = _redact_features(features)
    
    return features


def _extract_with_pdfplumber(pdf_path: Path) -> Dict[str, Any]:
    """Extract features using pdfplumber."""
    features = {
        'tool': 'pdfplumber',
        'filename': pdf_path.name,
        'page_count': 0,
        'header_tokens': [],
        'table_headers': [],
        'date_formats': [],
        'amount_formats': [],
        'geometry': [],
        'text_density': [],
        'metadata': {}
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        features['page_count'] = len(pdf.pages)
        features['metadata'] = pdf.metadata or {}
        
        # Extract from first page (most informative for templates)
        if len(pdf.pages) > 0:
            first_page = pdf.pages[0]
            
            # Extract text
            text = first_page.extract_text() or ''
            
            # Find header tokens (first 30% of page)
            page_height = first_page.height
            header_region = first_page.within_bbox((0, 0, first_page.width, page_height * 0.3))
            header_text = header_region.extract_text() or ''
            
            features['header_tokens'] = _extract_tokens(header_text)
            
            # Extract table information
            tables = first_page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 0:
                        # Extract header row candidates
                        header_row = table[0]
                        clean_headers = [str(h).strip() if h else '' for h in header_row]
                        features['table_headers'].append(clean_headers)
            
            # Detect date formats
            features['date_formats'] = _detect_date_formats(text)
            
            # Detect amount formats
            features['amount_formats'] = _detect_amount_formats(text)
            
            # Extract geometry bands (vertical regions)
            features['geometry'] = _extract_geometry_bands(first_page)
            
            # Text density by region
            features['text_density'] = _compute_text_density(first_page)
    
    return features


def _extract_with_pymupdf(pdf_path: Path) -> Dict[str, Any]:
    """Extract features using PyMuPDF."""
    features = {
        'tool': 'pymupdf',
        'filename': pdf_path.name,
        'page_count': 0,
        'header_tokens': [],
        'table_headers': [],
        'date_formats': [],
        'amount_formats': [],
        'geometry': [],
        'text_density': [],
        'metadata': {}
    }
    
    doc = fitz.open(pdf_path)
    features['page_count'] = len(doc)
    features['metadata'] = doc.metadata
    
    if len(doc) > 0:
        first_page = doc[0]
        text = first_page.get_text()
        
        # Extract header region (top 30%)
        page_height = first_page.rect.height
        header_rect = fitz.Rect(0, 0, first_page.rect.width, page_height * 0.3)
        header_text = first_page.get_text(clip=header_rect)
        
        features['header_tokens'] = _extract_tokens(header_text)
        
        # Detect date formats
        features['date_formats'] = _detect_date_formats(text)
        
        # Detect amount formats
        features['amount_formats'] = _detect_amount_formats(text)
        
        # Extract text blocks for geometry
        blocks = first_page.get_text("dict")["blocks"]
        features['geometry'] = _extract_geometry_from_blocks(blocks, page_height)
    
    doc.close()
    return features


def _extract_tokens(text: str, max_sample_chars: int = 500) -> List[str]:
    """
    Extract meaningful tokens from text.
    
    Args:
        text: Text to extract from
        max_sample_chars: Maximum characters to sample
    
    Returns:
        List of tokens found
    """
    # Limit text sample
    text = text[:max_sample_chars]
    
    # Convert to lowercase for matching
    text_lower = text.lower()
    
    # Find bank keywords
    tokens = []
    for keyword in BANK_KEYWORDS:
        if keyword in text_lower:
            tokens.append(keyword)
    
    # Find common bank names (partial matches)
    bank_names = ['chase', 'wells fargo', 'bank of america', 'citi', 'capital one', 
                  'us bank', 'pnc', 'fifth third', 'ally', 'schwab']
    for bank in bank_names:
        if bank in text_lower:
            tokens.append(f"bank:{bank}")
    
    return list(set(tokens))  # Deduplicate


def _detect_date_formats(text: str) -> List[str]:
    """
    Detect date format patterns in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of detected date format names
    """
    detected = []
    for pattern, format_name in DATE_PATTERNS:
        if re.search(pattern, text):
            detected.append(format_name)
    return list(set(detected))


def _detect_amount_formats(text: str) -> List[str]:
    """
    Detect amount/currency format patterns.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of detected amount format names
    """
    detected = []
    for pattern, format_name in AMOUNT_PATTERNS:
        if re.search(pattern, text):
            detected.append(format_name)
    return list(set(detected))


def _extract_geometry_bands(page) -> List[Dict[str, Any]]:
    """
    Extract vertical geometry bands from pdfplumber page.
    
    Returns:
        List of geometry band descriptions
    """
    bands = []
    
    # Divide page into horizontal bands
    page_height = page.height
    band_count = 5
    band_height = page_height / band_count
    
    for i in range(band_count):
        y_start = i * band_height
        y_end = (i + 1) * band_height
        
        band_region = page.within_bbox((0, y_start, page.width, y_end))
        band_text = band_region.extract_text() or ''
        
        bands.append({
            'band_index': i,
            'y_start_pct': round(y_start / page_height, 2),
            'y_end_pct': round(y_end / page_height, 2),
            'char_count': len(band_text),
            'has_tables': len(band_region.extract_tables()) > 0,
        })
    
    return bands


def _extract_geometry_from_blocks(blocks: List[Dict], page_height: float) -> List[Dict[str, Any]]:
    """
    Extract geometry from PyMuPDF blocks.
    
    Args:
        blocks: PyMuPDF text blocks
        page_height: Page height
    
    Returns:
        List of geometry band descriptions
    """
    bands = []
    band_count = 5
    band_height = page_height / band_count
    
    # Count blocks per band
    for i in range(band_count):
        y_start = i * band_height
        y_end = (i + 1) * band_height
        
        blocks_in_band = [
            b for b in blocks
            if b.get('type') == 0  # Text block
            and y_start <= b['bbox'][1] < y_end
        ]
        
        total_chars = sum(len(b.get('lines', [])) for b in blocks_in_band)
        
        bands.append({
            'band_index': i,
            'y_start_pct': round(y_start / page_height, 2),
            'y_end_pct': round(y_end / page_height, 2),
            'block_count': len(blocks_in_band),
            'char_count': total_chars,
        })
    
    return bands


def _compute_text_density(page) -> List[Dict[str, float]]:
    """
    Compute text density by region.
    
    Args:
        page: pdfplumber page
    
    Returns:
        List of density measurements
    """
    densities = []
    
    # Divide page into grid
    rows, cols = 3, 2
    cell_width = page.width / cols
    cell_height = page.height / rows
    
    for row in range(rows):
        for col in range(cols):
            x0 = col * cell_width
            y0 = row * cell_height
            x1 = x0 + cell_width
            y1 = y0 + cell_height
            
            cell = page.within_bbox((x0, y0, x1, y1))
            text = cell.extract_text() or ''
            
            area = cell_width * cell_height
            density = len(text) / area if area > 0 else 0
            
            densities.append({
                'row': row,
                'col': col,
                'density': round(density, 4),
            })
    
    return densities


def _redact_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact PII from extracted features.
    
    Args:
        features: Features dictionary
    
    Returns:
        Features with PII redacted
    """
    # Redact header tokens
    if 'header_tokens' in features:
        features['header_tokens'] = [
            redact_pii(token) if isinstance(token, str) else token
            for token in features['header_tokens']
        ]
    
    # Redact table headers
    if 'table_headers' in features:
        features['table_headers'] = [
            [redact_pii(h) if isinstance(h, str) else h for h in headers]
            for headers in features['table_headers']
        ]
    
    # Redact metadata
    if 'metadata' in features:
        # Remove sensitive metadata fields
        sensitive_fields = ['Author', 'Creator', 'Producer', 'Subject', 'Title']
        for field in sensitive_fields:
            if field in features['metadata']:
                del features['metadata'][field]
    
    return features


if __name__ == '__main__':
    """Test feature extraction."""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python sample_feature_extractor.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        features = extract_features(pdf_path, redact_pii=True)
        print(json.dumps(features, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



