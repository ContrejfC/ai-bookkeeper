"""
Tesseract OCR Provider (S11.1 True OCR)

Local Tesseract engine for token-level bounding box extraction.
"""
import os
import logging
from typing import List
from pathlib import Path

from .base import OCRProviderInterface, TokenBox, FieldBox

logger = logging.getLogger(__name__)


class TesseractProvider(OCRProviderInterface):
    """
    Tesseract OCR provider for local token extraction.
    
    Requires: tesseract-ocr installed, pytesseract, Pillow
    """
    
    def __init__(self, lang='eng'):
        self.lang = lang
        self._check_availability()
    
    def _check_availability(self):
        """Check if Tesseract is available."""
        try:
            import pytesseract
            from PIL import Image
            # Try to get version
            pytesseract.get_tesseract_version()
            self._available = True
        except:
            self._available = False
            logger.warning("Tesseract not available. Install: brew install tesseract && pip install pytesseract pillow")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    @property
    def provider_name(self) -> str:
        return "tesseract"
    
    def extract_tokens(self, image_path: str) -> List[TokenBox]:
        """
        Extract token-level bounding boxes using Tesseract.
        
        Returns normalized coordinates (0-1) for portability.
        """
        if not self.is_available:
            raise RuntimeError("Tesseract not available")
        
        import pytesseract
        from PIL import Image
        
        # Load image
        img = Image.open(image_path)
        width, height = img.size
        
        # Extract detailed data with bboxes
        data = pytesseract.image_to_data(
            img,
            lang=self.lang,
            output_type=pytesseract.Output.DICT
        )
        
        tokens = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if not text:
                continue
            
            # Normalize coordinates to 0-1
            x = data['left'][i] / width
            y = data['top'][i] / height
            w = data['width'][i] / width
            h = data['height'][i] / height
            
            # Confidence is 0-100, normalize to 0-1
            conf = data['conf'][i] / 100.0 if data['conf'][i] >= 0 else 0.0
            
            tokens.append(TokenBox(
                text=text,
                x=max(0, min(x, 1)),
                y=max(0, min(y, 1)),
                w=max(0, min(w, 1)),
                h=max(0, min(h, 1)),
                confidence=max(0, min(conf, 1)),
                page=0
            ))
        
        logger.info(f"Tesseract extracted {len(tokens)} tokens from {Path(image_path).name}")
        return tokens
    
    def extract_fields(self, image_path: str) -> List[FieldBox]:
        """
        Extract structured fields with bounding boxes.
        
        Uses existing parser logic to identify fields,
        then matches to token boxes.
        """
        if not self.is_available:
            raise RuntimeError("Tesseract not available")
        
        # Get all tokens
        tokens = self.extract_tokens(image_path)
        
        if not tokens:
            return []
        
        # Use existing parser to identify field values
        from app.ocr.parser import OCRParser
        import random
        
        parser = OCRParser()
        
        # Reconstruct text from tokens
        text = ' '.join([t.text for t in tokens])
        
        # Extract field values
        rng = random.Random(42)  # Deterministic
        fields_dict = parser._extract_fields(text, rng)
        
        # Match fields to tokens and aggregate bboxes
        field_boxes = []
        
        for field_name in ['date', 'amount', 'vendor', 'total']:
            value = fields_dict.get(field_name)
            if not value:
                continue
            
            # Find tokens that match this field value
            value_str = str(value).lower()
            matching_tokens = []
            
            for token in tokens:
                token_lower = token.text.lower()
                # Match if token is part of value or vice versa
                if (token_lower in value_str or value_str in token_lower or
                    # For amounts, match digits
                    (field_name in ['amount', 'total'] and any(c.isdigit() for c in token.text))):
                    matching_tokens.append(token)
            
            if matching_tokens:
                # Aggregate bounding box from matching tokens
                min_x = min(t.x for t in matching_tokens)
                min_y = min(t.y for t in matching_tokens)
                max_x = max(t.x + t.w for t in matching_tokens)
                max_y = max(t.y + t.h for t in matching_tokens)
                
                # Average confidence
                avg_conf = sum(t.confidence for t in matching_tokens) / len(matching_tokens)
                
                field_boxes.append(FieldBox(
                    field=field_name,
                    value=value,
                    x=min_x,
                    y=min_y,
                    w=max_x - min_x,
                    h=max_y - min_y,
                    confidence=avg_conf,
                    page=0,
                    tokens=matching_tokens
                ))
        
        logger.info(f"Extracted {len(field_boxes)} fields from {Path(image_path).name}")
        return field_boxes

