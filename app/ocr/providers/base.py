"""
OCR Provider Interface (S11.1 True OCR)

Abstract base class for OCR engine providers.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TokenBox:
    """
    Token-level bounding box from OCR engine.
    
    Coordinates normalized to 0-1 range for portability.
    """
    text: str
    x: float  # Normalized 0-1 (left edge)
    y: float  # Normalized 0-1 (top edge)
    w: float  # Normalized 0-1 (width)
    h: float  # Normalized 0-1 (height)
    confidence: float  # 0-1
    page: int = 0


@dataclass
class FieldBox:
    """
    Field-level bounding box (aggregated from tokens).
    
    Represents a semantic field (date, amount, vendor, total)
    with its source tokens for traceability.
    """
    field: str  # date, amount, vendor, total
    value: any  # Parsed value
    x: float  # Aggregated bbox (min x of tokens)
    y: float
    w: float
    h: float
    confidence: float  # Average of token confidences
    page: int = 0
    tokens: List[TokenBox] = None  # Source tokens
    
    def __post_init__(self):
        if self.tokens is None:
            self.tokens = []


class OCRProviderInterface(ABC):
    """
    Abstract interface for OCR providers.
    
    Allows swapping between Tesseract, Google Vision, AWS Textract, etc.
    """
    
    @abstractmethod
    def extract_tokens(self, image_path: str) -> List[TokenBox]:
        """
        Extract all text tokens with bounding boxes.
        
        Args:
            image_path: Path to image file (JPEG, PNG, PDF page, etc.)
            
        Returns:
            List of TokenBox objects with normalized coordinates
        """
        pass
    
    @abstractmethod
    def extract_fields(self, image_path: str) -> List[FieldBox]:
        """
        Extract structured fields (date, amount, vendor, total).
        
        Combines OCR token extraction with field detection logic.
        
        Args:
            image_path: Path to receipt image
            
        Returns:
            List of FieldBox objects for detected fields
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (tesseract, google_vision, aws_textract, etc.)."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (dependencies installed, credentials set, etc.)."""
        pass


def calculate_iou(box1: tuple, box2: tuple) -> float:
    """
    Calculate Intersection over Union (IoU) for two bounding boxes.
    
    Args:
        box1: (x, y, w, h) normalized coordinates
        box2: (x, y, w, h) normalized coordinates
        
    Returns:
        IoU score (0-1)
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    # Convert to (x1, y1, x2, y2) format
    box1_x2 = x1 + w1
    box1_y2 = y1 + h1
    box2_x2 = x2 + w2
    box2_y2 = y2 + h2
    
    # Calculate intersection
    inter_x1 = max(x1, x2)
    inter_y1 = max(y1, y2)
    inter_x2 = min(box1_x2, box2_x2)
    inter_y2 = min(box1_y2, box2_y2)
    
    if inter_x2 < inter_x1 or inter_y2 < inter_y1:
        return 0.0
    
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    
    # Calculate union
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area

