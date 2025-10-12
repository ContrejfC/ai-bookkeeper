"""
OCR Parser for receipt/document extraction.

Supports:
- Pytesseract (local) with pluggable cloud OCR (Google Vision, AWS Textract)
- Field extraction: vendor, amount, date, category
- Per-field confidence scoring
- Multiple date/amount format normalization
"""
import re
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from abc import ABC, abstractmethod

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available - install with: pip install pytesseract pillow")

logger = logging.getLogger(__name__)


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, overall_confidence)
        """
        pass


class TesseractOCR(OCRProvider):
    """Pytesseract-based OCR provider."""
    
    def __init__(self, config: str = "--psm 6"):
        """
        Initialize Tesseract OCR.
        
        Args:
            config: Tesseract configuration string
        """
        if not PYTESSERACT_AVAILABLE:
            raise ImportError("pytesseract not installed")
        self.config = config
    
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extract text using Tesseract."""
        try:
            image = Image.open(image_path)
            
            # Get detailed data for confidence
            data = pytesseract.image_to_data(image, config=self.config, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            # Extract text
            text = pytesseract.image_to_string(image, config=self.config)
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return "", 0.0


class GoogleVisionOCR(OCRProvider):
    """Google Cloud Vision OCR provider (stub)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.warning("Google Vision OCR not implemented - using stub")
    
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extract text using Google Vision API (stub)."""
        # TODO: Implement Google Vision API integration
        raise NotImplementedError("Google Vision OCR not implemented")


class AWSTextractOCR(OCRProvider):
    """AWS Textract OCR provider (stub)."""
    
    def __init__(self, aws_access_key: str, aws_secret_key: str):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        logger.warning("AWS Textract OCR not implemented - using stub")
    
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extract text using AWS Textract (stub)."""
        # TODO: Implement AWS Textract integration
        raise NotImplementedError("AWS Textract OCR not implemented")


class OCRParser:
    """
    Main OCR parser for receipt/document extraction.
    
    Extracts structured fields with confidence scores.
    """
    
    def __init__(self, provider: Optional[OCRProvider] = None):
        """
        Initialize OCR parser.
        
        Args:
            provider: OCR provider instance (defaults to TesseractOCR)
        """
        if provider is None:
            if PYTESSERACT_AVAILABLE:
                provider = TesseractOCR()
            else:
                logger.error("No OCR provider available")
                raise RuntimeError("No OCR provider available")
        
        self.provider = provider
    
    def parse_document(self, image_path: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse document and extract structured fields.
        
        Args:
            image_path: Path to image file
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Structured OCR payload with fields and confidence scores
        """
        if document_id is None:
            document_id = uuid.uuid4().hex
        
        logger.info(f"Parsing document {document_id}: {image_path}")
        
        # Extract text
        raw_text, overall_confidence = self.provider.extract_text(image_path)
        
        if not raw_text:
            logger.warning(f"No text extracted from {image_path}")
            return {
                "document_id": document_id,
                "status": "failed",
                "error": "No text extracted",
                "fields": {},
                "raw": {"text": "", "confidence": 0.0}
            }
        
        # Extract fields
        fields = self._extract_fields(raw_text, overall_confidence)
        
        return {
            "document_id": document_id,
            "status": "success",
            "fields": fields,
            "raw": {
                "text": raw_text,
                "confidence": overall_confidence
            }
        }
    
    def _extract_fields(self, text: str, base_confidence: float) -> Dict[str, Dict[str, Any]]:
        """
        Extract structured fields from OCR text.
        
        Args:
            text: Raw OCR text
            base_confidence: Base confidence from OCR
            
        Returns:
            Dict of fields with values and confidence scores
        """
        fields = {}
        
        # Extract vendor (usually first lines)
        vendor, vendor_conf = self._extract_vendor(text, base_confidence)
        if vendor:
            fields["vendor"] = {"value": vendor, "confidence": vendor_conf}
        
        # Extract amount (look for currency patterns)
        amount, amount_conf = self._extract_amount(text, base_confidence)
        if amount is not None:
            fields["amount"] = {"value": amount, "confidence": amount_conf}
        
        # Extract date (look for date patterns)
        date, date_conf = self._extract_date(text, base_confidence)
        if date:
            fields["date"] = {"value": date, "confidence": date_conf}
        
        # Extract category (heuristic based on keywords)
        category, category_conf = self._extract_category(text, base_confidence)
        if category:
            fields["category"] = {"value": category, "confidence": category_conf}
        
        return fields
    
    def _extract_vendor(self, text: str, base_conf: float) -> Tuple[Optional[str], float]:
        """Extract vendor name from text."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return None, 0.0
        
        # Heuristic: Vendor is usually in first 2-3 lines, longest or contains keywords
        candidates = []
        for i, line in enumerate(lines[:5]):
            # Skip common non-vendor patterns
            if any(skip in line.lower() for skip in ['receipt', 'invoice', 'date', 'total', 'subtotal', 'tax']):
                continue
            
            # Prefer lines with reasonable length
            if 3 <= len(line) <= 50:
                # Boost confidence for first lines
                confidence = base_conf * (1.0 - i * 0.05)
                candidates.append((line, confidence))
        
        if candidates:
            # Return highest confidence
            vendor, conf = max(candidates, key=lambda x: x[1])
            return vendor, min(conf, 0.95)
        
        return None, 0.0
    
    def _extract_amount(self, text: str, base_conf: float) -> Tuple[Optional[float], float]:
        """Extract amount from text."""
        # Patterns: $123.45, 123.45, $123, etc.
        patterns = [
            r'\$\s*(\d{1,6}[,\.]?\d{0,3}\.?\d{2})',  # $123.45
            r'(?:total|amount|sum)[\s:]*\$?\s*(\d{1,6}[,\.]?\d{0,3}\.?\d{2})',  # Total: $123.45
            r'(\d{1,6}\.\d{2})\s*(?:USD|$)',  # 123.45 USD
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean amount string
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    
                    # Sanity check
                    if 0.01 <= amount <= 999999:
                        # Boost confidence if near "total" keyword
                        context = text[max(0, match.start()-20):match.end()+20].lower()
                        conf_boost = 0.1 if 'total' in context else 0.0
                        confidence = min(base_conf + conf_boost, 0.98)
                        amounts.append((amount, confidence))
                except ValueError:
                    continue
        
        if amounts:
            # Return highest confidence or largest amount if similar confidence
            best = max(amounts, key=lambda x: (x[1], x[0]))
            return best[0], best[1]
        
        return None, 0.0
    
    def _extract_date(self, text: str, base_conf: float) -> Tuple[Optional[str], float]:
        """Extract date from text."""
        # Multiple date patterns
        patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # 10/08/2025 or 10-08-2025
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2025-10-08
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',  # 8 Oct 2025
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    # Boost confidence if near "date" keyword
                    context = text[max(0, match.start()-10):match.end()+10].lower()
                    conf_boost = 0.1 if 'date' in context else 0.0
                    confidence = min(base_conf + conf_boost, 0.95)
                    dates.append((parsed_date, confidence))
        
        if dates:
            best = max(dates, key=lambda x: x[1])
            return best[0], best[1]
        
        return None, 0.0
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into YYYY-MM-DD format."""
        formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y', '%b %d %Y', '%B %d %Y',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _extract_category(self, text: str, base_conf: float) -> Tuple[Optional[str], float]:
        """Extract category from text using keyword matching."""
        text_lower = text.lower()
        
        # Category keywords (heuristic)
        categories = {
            'Office Supplies': ['staples', 'office depot', 'paper', 'pen', 'printer', 'toner'],
            'Food & Dining': ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'burger', 'pizza'],
            'Transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking'],
            'Utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            'Software': ['aws', 'github', 'adobe', 'microsoft', 'software', 'saas', 'subscription'],
            'Marketing': ['google ads', 'facebook', 'advertising', 'marketing', 'linkedin'],
        }
        
        best_category = None
        best_score = 0.0
        
        for category, keywords in categories.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > best_score:
                best_score = matches
                best_category = category
        
        if best_category:
            # Lower confidence for category (it's a guess)
            confidence = min(base_conf * 0.7, 0.75)
            return best_category, confidence
        
        return None, 0.0


def get_ocr_provider(provider_name: str = "tesseract", **kwargs) -> OCRProvider:
    """
    Factory function to get OCR provider.
    
    Args:
        provider_name: Name of provider (tesseract, google_vision, aws_textract)
        **kwargs: Provider-specific arguments
        
    Returns:
        OCRProvider instance
    """
    if provider_name == "tesseract":
        return TesseractOCR(config=kwargs.get("config", "--psm 6"))
    elif provider_name == "google_vision":
        return GoogleVisionOCR(api_key=kwargs.get("api_key", ""))
    elif provider_name == "aws_textract":
        return AWSTextractOCR(
            aws_access_key=kwargs.get("aws_access_key", ""),
            aws_secret_key=kwargs.get("aws_secret_key", "")
        )
    else:
        raise ValueError(f"Unknown OCR provider: {provider_name}")

