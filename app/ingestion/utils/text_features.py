"""
Text Feature Extraction
=======================

Extract text features from PDFs for template matching.
"""

import logging
from typing import Dict, List, Any, Optional
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

logger = logging.getLogger(__name__)


def extract_text_features(pdf_path: Path, max_pages: int = 2) -> Dict[str, Any]:
    """
    Extract text features from a PDF for template matching.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process (default: 2, usually enough)
    
    Returns:
        Dictionary of features:
        {
            'header_text': str,
            'footer_text': str,
            'table_headers': List[List[str]],
            'geometry': {
                'header_band': [start_pct, end_pct],
                'table_band': [start_pct, end_pct]
            },
            'text_density': float,
            'page_count': int
        }
    """
    if not HAS_PDFPLUMBER and not HAS_PYMUPDF:
        raise ImportError("Neither pdfplumber nor PyMuPDF is installed")
    
    # Use pdfplumber if available (better table detection)
    if HAS_PDFPLUMBER:
        return _extract_with_pdfplumber(pdf_path, max_pages)
    else:
        return _extract_with_pymupdf(pdf_path, max_pages)


def _extract_with_pdfplumber(pdf_path: Path, max_pages: int) -> Dict[str, Any]:
    """Extract features using pdfplumber."""
    features = {
        'header_text': '',
        'footer_text': '',
        'table_headers': [],
        'geometry': {},
        'text_density': 0.0,
        'page_count': 0
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        features['page_count'] = len(pdf.pages)
        
        # Process first page (most informative for templates)
        if len(pdf.pages) > 0:
            first_page = pdf.pages[0]
            page_height = first_page.height
            page_width = first_page.width
            
            # Extract header region (top 20%)
            header_region = first_page.within_bbox((0, 0, page_width, page_height * 0.20))
            header_text = header_region.extract_text() or ''
            features['header_text'] = header_text.strip()
            
            # Extract footer region (bottom 15%)
            footer_region = first_page.within_bbox((0, page_height * 0.85, page_width, page_height))
            footer_text = footer_region.extract_text() or ''
            features['footer_text'] = footer_text.strip()
            
            # Extract table information
            tables = first_page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 0:
                        # Extract header row
                        header_row = table[0]
                        clean_headers = [str(h).strip() if h else '' for h in header_row]
                        if any(clean_headers):  # Only add if non-empty
                            features['table_headers'].append(clean_headers)
                
                # Try to detect table geometry
                if tables:
                    # Find first table
                    table_bbox = first_page.find_tables()[0].bbox if first_page.find_tables() else None
                    if table_bbox:
                        y_top = table_bbox[1]
                        y_bottom = table_bbox[3]
                        features['geometry']['table_band'] = [
                            y_top / page_height,
                            y_bottom / page_height
                        ]
            
            # Compute text density
            full_text = first_page.extract_text() or ''
            area = page_width * page_height
            features['text_density'] = len(full_text) / area if area > 0 else 0
            
            # Add geometry hints
            features['geometry']['header_band'] = [0.0, 0.20]
            if 'table_band' not in features['geometry']:
                # Default table band if not detected
                features['geometry']['table_band'] = [0.25, 0.80]
    
    return features


def _extract_with_pymupdf(pdf_path: Path, max_pages: int) -> Dict[str, Any]:
    """Extract features using PyMuPDF."""
    features = {
        'header_text': '',
        'footer_text': '',
        'table_headers': [],
        'geometry': {},
        'text_density': 0.0,
        'page_count': 0
    }
    
    doc = fitz.open(pdf_path)
    features['page_count'] = len(doc)
    
    if len(doc) > 0:
        first_page = doc[0]
        page_height = first_page.rect.height
        page_width = first_page.rect.width
        
        # Extract header region (top 20%)
        header_rect = fitz.Rect(0, 0, page_width, page_height * 0.20)
        header_text = first_page.get_text(clip=header_rect)
        features['header_text'] = header_text.strip()
        
        # Extract footer region (bottom 15%)
        footer_rect = fitz.Rect(0, page_height * 0.85, page_width, page_height)
        footer_text = first_page.get_text(clip=footer_rect)
        features['footer_text'] = footer_text.strip()
        
        # Try to detect tables (PyMuPDF has basic table detection)
        # For simplicity, we'll extract text blocks and look for grid patterns
        blocks = first_page.get_text("dict")["blocks"]
        
        # Look for text blocks with regular spacing (potential table rows)
        text_blocks = [b for b in blocks if b.get('type') == 0]
        if text_blocks:
            # Simple heuristic: if we have blocks in the middle region, assume table
            middle_blocks = [
                b for b in text_blocks
                if 0.20 * page_height < b['bbox'][1] < 0.85 * page_height
            ]
            if middle_blocks:
                features['geometry']['table_band'] = [0.25, 0.80]
        
        # Compute text density
        full_text = first_page.get_text()
        area = page_width * page_height
        features['text_density'] = len(full_text) / area if area > 0 else 0
        
        # Add geometry hints
        features['geometry']['header_band'] = [0.0, 0.20]
        if 'table_band' not in features['geometry']:
            features['geometry']['table_band'] = [0.25, 0.80]
    
    doc.close()
    return features


def extract_table_headers_from_text(text: str) -> List[str]:
    """
    Extract potential table headers from text using heuristics.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of potential header keywords
    """
    common_headers = [
        'date', 'description', 'amount', 'balance', 'debit', 'credit',
        'transaction', 'posting', 'deposits', 'withdrawals', 'reference',
        'check', 'number', 'type', 'category'
    ]
    
    text_lower = text.lower()
    found_headers = []
    
    for header in common_headers:
        if header in text_lower:
            found_headers.append(header)
    
    return found_headers


def normalize_header_text(text: str) -> str:
    """
    Normalize header text for matching.
    
    Args:
        text: Raw header text
    
    Returns:
        Normalized text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Lowercase for case-insensitive matching
    text = text.lower()
    
    return text


if __name__ == '__main__':
    """Test feature extraction."""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python text_features.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    try:
        features = extract_text_features(pdf_path)
        print(json.dumps(features, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



