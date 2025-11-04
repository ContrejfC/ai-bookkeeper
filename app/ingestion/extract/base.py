"""
Extraction Base Protocol
========================

Base interface and context for all extractors (CSV, OFX, PDF, OCR).
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol, List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionContext:
    """
    Context passed to extractors with file info and configuration.
    """
    file_path: Path
    mime_type: str
    file_size: int
    tenant_id: str
    account_hint: Optional[str] = None
    
    # Configuration flags
    ocr_enabled: bool = True
    malware_checked: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    start_time: float = 0.0


@dataclass
class ExtractionResult:
    """
    Result from an extractor with raw transactions and metadata.
    """
    success: bool
    raw_transactions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Extraction metadata
    extraction_method: str = "unknown"
    confidence: float = 0.5
    pages_processed: Optional[int] = None
    ocr_pages: Optional[int] = None
    extraction_time_ms: int = 0
    
    # Detection results
    detected_bank: Optional[str] = None
    detected_account: Optional[str] = None
    detected_period: Optional[Dict[str, str]] = None
    
    # Quality indicators
    header_match_score: Optional[float] = None
    table_confidence: Optional[float] = None
    ocr_char_confidence: Optional[float] = None
    
    # Errors
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class Extractor(Protocol):
    """
    Protocol for file extractors.
    
    All extractors must implement can_handle() and extract() methods.
    """
    
    def can_handle(self, context: ExtractionContext) -> bool:
        """
        Check if this extractor can handle the given file.
        
        Args:
            context: Extraction context with file info
        
        Returns:
            True if this extractor can process the file
        """
        ...
    
    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """
        Extract transactions from the file.
        
        Args:
            context: Extraction context
        
        Returns:
            ExtractionResult with raw transactions and metadata
        """
        ...


class BaseExtractor:
    """
    Base class with common extractor functionality.
    
    Provides utilities for concrete extractors to use.
    """
    
    def __init__(self, name: str):
        """
        Initialize base extractor.
        
        Args:
            name: Extractor name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def log_start(self, context: ExtractionContext):
        """Log extraction start."""
        self.logger.info(
            f"Starting {self.name} extraction: {context.file_path.name} "
            f"({context.mime_type}, {context.file_size} bytes)"
        )
    
    def log_end(self, result: ExtractionResult):
        """Log extraction end."""
        if result.success:
            self.logger.info(
                f"Completed {self.name} extraction: "
                f"{len(result.raw_transactions)} transactions, "
                f"confidence: {result.confidence:.2f}, "
                f"time: {result.extraction_time_ms}ms"
            )
        else:
            self.logger.error(
                f"Failed {self.name} extraction: {result.error}"
            )
    
    def create_error_result(self, error_message: str) -> ExtractionResult:
        """
        Create an error result.
        
        Args:
            error_message: Error message
        
        Returns:
            ExtractionResult with error
        """
        return ExtractionResult(
            success=False,
            extraction_method=self.name,
            error=error_message
        )



