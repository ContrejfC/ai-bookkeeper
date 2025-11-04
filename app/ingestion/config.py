"""
Ingestion Pipeline Configuration
=================================

Size limits, accepted types, feature flags, and timeouts for the ingestion pipeline.
"""

import os
from typing import List
from pydantic import BaseModel, Field


class IngestionConfig(BaseModel):
    """Configuration for the ingestion pipeline."""
    
    # File size limits (in bytes)
    MAX_CSV_SIZE: int = Field(default=10 * 1024 * 1024, description="10MB")
    MAX_PDF_SIZE: int = Field(default=50 * 1024 * 1024, description="50MB")
    MAX_IMAGE_SIZE: int = Field(default=25 * 1024 * 1024, description="25MB")
    MAX_ZIP_SIZE: int = Field(default=200 * 1024 * 1024, description="200MB")
    MAX_OFX_SIZE: int = Field(default=10 * 1024 * 1024, description="10MB")
    
    # Row limits
    MAX_CSV_ROWS: int = Field(default=100000, description="Max rows per CSV")
    MAX_TRANSACTIONS_PER_FILE: int = Field(default=100000, description="Max transactions")
    
    # Accepted MIME types
    ACCEPTED_TYPES: List[str] = Field(default=[
        "text/csv",
        "application/csv",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/zip",
        "application/x-zip-compressed",
        "application/ofx",
        "application/x-ofx",
        "application/qfx",
        "application/vnd.intu.qfx",
    ])
    
    # Feature flags
    OCR_ENABLED: bool = Field(
        default=os.getenv("OCR_ENABLED", "true").lower() == "true",
        description="Enable OCR for scanned PDFs and images"
    )
    
    MALWARE_SCAN_ENABLED: bool = Field(
        default=os.getenv("MALWARE_SCAN_ENABLED", "false").lower() == "true",
        description="Enable ClamAV malware scanning"
    )
    
    # OCR configuration
    TESSDATA_PREFIX: str = Field(
        default=os.getenv("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/4.00/tessdata"),
        description="Tesseract data directory"
    )
    
    TESSERACT_LANG: str = Field(default="eng", description="Tesseract language")
    
    OCR_DPI: int = Field(default=300, description="DPI for OCR preprocessing")
    
    # Timeouts (in seconds)
    PDF_EXTRACTION_TIMEOUT: int = Field(default=120, description="Timeout for PDF extraction")
    OCR_PAGE_TIMEOUT: int = Field(default=30, description="Timeout per OCR page")
    CSV_PARSE_TIMEOUT: int = Field(default=60, description="Timeout for CSV parsing")
    
    # Reconciliation settings
    BALANCE_TOLERANCE: float = Field(default=0.01, description="Balance check tolerance ($)")
    REQUIRE_RECONCILIATION: bool = Field(default=True, description="Require reconciliation to pass")
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLD_REVIEW: float = Field(
        default=0.85,
        description="Confidence below this triggers manual review"
    )
    
    # Deduplication
    DEDUP_FINGERPRINT_ROUND_DECIMALS: int = Field(
        default=2,
        description="Round amounts to N decimals for fingerprinting"
    )
    
    # Artifact settings
    SAVE_ARTIFACTS: bool = Field(default=True, description="Save extraction artifacts")
    ARTIFACT_SAMPLE_ROWS: int = Field(default=2, description="Number of sample rows to save")
    
    # Storage
    TEMP_DIR: str = Field(
        default=os.getenv("TEMP_DIR", "/tmp/ingestion"),
        description="Temporary directory for file processing"
    )
    
    ARTIFACT_DIR: str = Field(
        default=os.getenv("ARTIFACT_DIR", "/var/ingestion/artifacts"),
        description="Directory for storing artifacts"
    )
    
    # Performance targets (for monitoring)
    TARGET_TEXT_PDF_P50_MS: int = Field(default=6000, description="6s p50 for 20-page PDF")
    TARGET_OCR_PAGE_P50_MS: int = Field(default=900, description="0.9s p50 per page")
    TARGET_MEMORY_MB: int = Field(default=512, description="512MB max per job")
    
    # Data retention
    RAW_FILE_RETENTION_DAYS: int = Field(default=30, description="Keep raw files for 30 days")
    
    class Config:
        env_prefix = "INGESTION_"


# Global configuration instance
config = IngestionConfig()



