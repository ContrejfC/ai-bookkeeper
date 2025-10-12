"""
OCR Parser stub for AI Bookkeeper (Sprint 9 Stage B).

Simulates OCR extraction from PDF receipts with realistic accuracy (≥90%).
In production, this would use Tesseract, Google Vision, or AWS Textract.

For testing purposes, we parse the original .txt files with simulated OCR errors.
"""
import re
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class OCRParser:
    """
    OCR Parser stub that simulates realistic field extraction.
    
    In production, this would use actual OCR engines. For testing,
    we extract from .txt with simulated errors.
    """
    
    def __init__(self, accuracy_target: float = 0.90):
        """
        Initialize OCR parser.
        
        Args:
            accuracy_target: Target field-level accuracy (default 90%)
        """
        self.accuracy_target = accuracy_target
        self.error_rate = 1.0 - accuracy_target
    
    def parse_pdf(self, pdf_path: Path, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse a PDF receipt and extract structured fields.
        
        For testing, reads the corresponding .txt file and extracts fields
        with simulated OCR errors.
        
        Args:
            pdf_path: Path to PDF file
            seed: Random seed for deterministic errors
            
        Returns:
            Dictionary with extracted fields: date, amount, vendor, total, confidence
        """
        rng = random.Random(seed) if seed is not None else random.Random()
        
        # Find corresponding .txt file
        # receipts_pdf/alpha/receipt_0001.pdf → receipts/alpha/receipt_0001.txt
        txt_path = self._get_txt_path(pdf_path)
        
        if not txt_path.exists():
            return {
                "date": None,
                "amount": None,
                "vendor": None,
                "total": None,
                "confidence": 0.0,
                "error": f"No .txt file found at {txt_path}"
            }
        
        # Read text
        with open(txt_path, "r") as f:
            text = f.read()
        
        # Extract fields
        fields = self._extract_fields(text, rng)
        
        return fields
    
    def _get_txt_path(self, pdf_path: Path) -> Path:
        """Get corresponding .txt path for a PDF."""
        # receipts_pdf/alpha/receipt_0001.pdf → receipts/alpha/receipt_0001.txt
        parts = pdf_path.parts
        tenant = parts[-2]  # 'alpha' or 'beta'
        filename = pdf_path.stem + ".txt"
        
        txt_dir = pdf_path.parent.parent.parent / "receipts" / tenant
        return txt_dir / filename
    
    def _extract_fields(self, text: str, rng: random.Random) -> Dict[str, Any]:
        """
        Extract fields from receipt text with simulated OCR errors.
        
        Simulates ≥90% accuracy per field.
        """
        # Date extraction
        date_match = re.search(r'Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        date_value = date_match.group(1) if date_match else None
        date_correct = rng.random() > self.error_rate
        if not date_correct and date_value:
            # Simulate OCR error in date
            date_value = self._corrupt_date(date_value, rng)
        
        # Amount extraction (first amount in text, often subtotal)
        amount_match = re.search(r'\$\s*(\d+[.,]\d{2})', text)
        amount_value = float(amount_match.group(1).replace(',', '')) if amount_match else None
        amount_correct = rng.random() > self.error_rate
        if not amount_correct and amount_value:
            # Simulate OCR error in amount
            amount_value = round(amount_value * rng.uniform(0.95, 1.05), 2)
        
        # Total extraction (look for "Total" keyword)
        total_match = re.search(r'Total[:\s]+\$\s*(\d+[.,]\d{2})', text, re.IGNORECASE)
        total_value = float(total_match.group(1).replace(',', '')) if total_match else None
        total_correct = rng.random() > self.error_rate
        if not total_correct and total_value:
            # Simulate OCR error in total
            total_value = round(total_value * rng.uniform(0.95, 1.05), 2)
        
        # Vendor extraction (first line or "From:" field)
        vendor_match = re.search(r'(?:From|INVOICE)[\s:]+([A-Za-z][A-Za-z\s&]+?)(?:\n|$|\s{2,})', text, re.IGNORECASE | re.MULTILINE)
        if not vendor_match:
            # Try first non-empty line
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            vendor_value = lines[0] if lines else None
        else:
            vendor_value = vendor_match.group(1).strip()
        
        vendor_correct = rng.random() > self.error_rate
        if not vendor_correct and vendor_value:
            # Simulate OCR error in vendor (typo)
            vendor_value = self._corrupt_text(vendor_value, rng)
        
        # Calculate overall confidence
        extracted_count = sum([
            date_value is not None,
            amount_value is not None,
            total_value is not None,
            vendor_value is not None
        ])
        correct_count = sum([
            date_value is not None and date_correct,
            amount_value is not None and amount_correct,
            total_value is not None and total_correct,
            vendor_value is not None and vendor_correct
        ])
        confidence = correct_count / extracted_count if extracted_count > 0 else 0.0
        
        return {
            "date": date_value,
            "amount": amount_value,
            "vendor": vendor_value,
            "total": total_value,
            "confidence": confidence,
            "extracted_fields": extracted_count,
            "correct_fields": correct_count
        }
    
    def _corrupt_date(self, date_str: str, rng: random.Random) -> str:
        """Simulate OCR error in date."""
        # Swap a digit
        chars = list(date_str)
        digit_positions = [i for i, c in enumerate(chars) if c.isdigit()]
        if digit_positions:
            pos = rng.choice(digit_positions)
            chars[pos] = str(rng.randint(0, 9))
        return ''.join(chars)
    
    def _corrupt_text(self, text: str, rng: random.Random) -> str:
        """Simulate OCR error in text."""
        if len(text) < 2:
            return text
        chars = list(text)
        # Swap one character
        pos = rng.randint(0, len(chars) - 2)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return ''.join(chars)


# Singleton instance
_parser = None

def get_parser() -> OCRParser:
    """Get global OCR parser instance."""
    global _parser
    if _parser is None:
        _parser = OCRParser(accuracy_target=0.90)
    return _parser


def get_ocr_provider():
    """
    Get configured OCR provider (S11.1).
    
    Returns provider instance or None for fallback to heuristic.
    """
    import os
    
    provider_name = os.getenv("OCR_PROVIDER", "tesseract")
    
    if provider_name == "tesseract":
        try:
            from app.ocr.providers.tesseract import TesseractProvider
            provider = TesseractProvider()
            if provider.is_available:
                return provider
            else:
                logger.warning("Tesseract configured but not available, using fallback")
                return None
        except ImportError:
            logger.warning("Tesseract provider not found, using fallback")
            return None
    
    elif provider_name == "google_vision":
        # Stub for future implementation
        logger.warning("Google Vision not implemented, using fallback")
        return None
    
    elif provider_name == "aws_textract":
        # Stub for future implementation
        logger.warning("AWS Textract not implemented, using fallback")
        return None
    
    else:
        logger.warning(f"Unknown OCR provider: {provider_name}, using fallback")
        return None


def extract_with_bboxes_v2(receipt_path: str) -> List:
    """
    Extract fields with TRUE token-level bounding boxes (S11.1).
    
    Uses configured OCR provider. Falls back to heuristic if unavailable.
    
    Args:
        receipt_path: Path to receipt image/PDF
        
    Returns:
        List of FieldBox objects (from provider) or dict (from fallback)
    """
    provider = get_ocr_provider()
    
    if provider:
        try:
            return provider.extract_fields(receipt_path)
        except Exception as e:
            logger.error(f"OCR provider failed: {e}, using fallback")
    
    # Fallback to heuristic (existing implementation)
    logger.info(f"Using heuristic bbox extraction for {receipt_path}")
    return extract_with_bboxes(receipt_path)


def extract_with_bboxes(receipt_path: str, text: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract fields with bounding box coordinates (Phase 2b - Receipt Highlights).
    
    Returns dict mapping field names to {value, bbox, confidence}.
    Bbox coordinates are normalized 0-1 for {x, y, w, h, page}.
    
    Args:
        receipt_path: Path to receipt file (for ID)
        text: Receipt text content (if None, reads from receipt_path)
        
    Returns:
        {
            "date": {"value": "10/11/2024", "bbox": {...}, "confidence": 0.95},
            "amount": {"value": 145.50, "bbox": {...}, "confidence": 0.98},
            ...
        }
    """
    # Read text if not provided
    if text is None:
        if not Path(receipt_path).exists():
            return {}
        with open(receipt_path, "r") as f:
            text = f.read()
    
    # Extract fields using existing parser
    parser = get_parser()
    rng = random.Random(42)  # Deterministic for testing
    fields_dict = parser._extract_fields(text, rng)
    
    lines = text.splitlines()
    total_lines = max(len(lines), 1)
    
    result = {}
    
    # Find bbox for each field
    for field_name in ['date', 'amount', 'vendor', 'total']:
        value = fields_dict.get(field_name)
        if not value:
            continue
        
        # Find line containing this value
        found = False
        for line_idx, line in enumerate(lines):
            search_str = str(value)
            if search_str in line:
                # Calculate normalized bbox (0-1 coordinates)
                y = line_idx / total_lines
                col_idx = line.find(search_str)
                x = col_idx / 80 if len(line) > 0 else 0.05  # Assume 80 char width
                w = min(len(search_str) / 80, 0.9)
                h = 1.0 / total_lines
                
                result[field_name] = {
                    "value": value,
                    "bbox": {
                        "x": min(max(x, 0.0), 0.95),
                        "y": min(max(y, 0.0), 0.95),
                        "w": min(w, 0.9),
                        "h": min(h, 0.2),
                        "page": 0
                    },
                    "confidence": fields_dict.get('confidence', 0.85)
                }
                found = True
                break
        
        # Fallback: approximate position if not found in exact line
        if not found and value:
            # Use heuristics: dates at top, amounts at bottom
            if field_name == 'date':
                y, x = 0.05, 0.1
            elif field_name in ['amount', 'total']:
                y, x = 0.85, 0.7
            else:  # vendor
                y, x = 0.02, 0.05
            
            result[field_name] = {
                "value": value,
                "bbox": {
                    "x": x,
                    "y": y,
                    "w": 0.3,
                    "h": 0.05,
                    "page": 0
                },
                "confidence": fields_dict.get('confidence', 0.70)  # Lower confidence
            }
    
    return result

