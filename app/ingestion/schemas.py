"""
Ingestion Pydantic Schemas
==========================

Request/response models and canonical transaction schema.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, constr, condecimal, validator
from uuid import UUID


class CanonicalTransaction(BaseModel):
    """
    Canonical normalized transaction schema.
    
    All extractors and normalizers must produce this format.
    """
    account_id: str = Field(..., description="Account number or identifier")
    post_date: date = Field(..., description="Transaction posting date")
    value_date: Optional[date] = Field(None, description="Value/effective date")
    description: str = Field(..., description="Transaction description/memo")
    amount: Decimal = Field(..., description="Signed amount (negative=debit, positive=credit)")
    balance: Optional[Decimal] = Field(None, description="Running balance after transaction")
    currency: constr(min_length=3, max_length=3) = Field(default="USD", description="ISO 4217 currency code")
    source: Literal["pdf", "csv", "ofx", "ocr", "image"] = Field(..., description="Extraction source")
    source_confidence: condecimal(ge=0, le=1) = Field(..., description="Extraction confidence (0.0-1.0)")
    
    # Optional metadata
    reference: Optional[str] = Field(None, description="Transaction reference number")
    category: Optional[str] = Field(None, description="Transaction category")
    vendor: Optional[str] = Field(None, description="Vendor/merchant name")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
        }
    
    @validator('currency')
    def currency_uppercase(cls, v):
        """Ensure currency code is uppercase."""
        return v.upper() if v else "USD"
    
    @validator('amount')
    def amount_not_zero(cls, v):
        """Ensure amount is not zero."""
        if v == 0:
            raise ValueError("Transaction amount cannot be zero")
        return v


class IngestionRequest(BaseModel):
    """Request to ingest a statement file."""
    tenant_id: UUID = Field(..., description="Tenant identifier")
    account_hint: Optional[str] = Field(None, description="Optional account number hint")
    force_reprocess: bool = Field(default=False, description="Force reprocessing if file already exists")
    skip_reconciliation: bool = Field(default=False, description="Skip reconciliation checks")
    skip_deduplication: bool = Field(default=False, description="Skip deduplication")


class IngestionResponse(BaseModel):
    """Response from ingestion upload."""
    file_id: UUID = Field(..., description="Unique file identifier (SHA-256 based)")
    job_id: Optional[UUID] = Field(None, description="Background job identifier")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Human-readable message")
    
    # Metrics (populated after processing)
    rows_extracted: Optional[int] = Field(None, description="Number of transactions extracted")
    rows_duplicates: Optional[int] = Field(None, description="Number of duplicates detected")
    confidence_avg: Optional[float] = Field(None, description="Average confidence score")
    needs_review_count: Optional[int] = Field(None, description="Transactions flagged for review")
    
    # Artifacts
    artifacts: Optional[List[Dict[str, Any]]] = Field(None, description="Extraction artifacts")
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
        }


class IngestionStatusResponse(BaseModel):
    """Status check response for a file or job."""
    file_id: UUID
    status: str
    progress: Optional[float] = Field(None, ge=0, le=1, description="Processing progress (0.0-1.0)")
    error: Optional[Dict[str, Any]] = None
    result: Optional[IngestionResponse] = None


class ExtractionMetadata(BaseModel):
    """Metadata from extraction process."""
    method: str = Field(..., description="Extraction method used")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    pages_processed: Optional[int] = None
    ocr_pages: Optional[int] = None
    extraction_time_ms: int = Field(..., description="Extraction time in milliseconds")
    
    # Detection results
    detected_bank: Optional[str] = None
    detected_account: Optional[str] = None
    detected_period: Optional[Dict[str, str]] = None
    
    # Quality indicators
    header_match_score: Optional[float] = Field(None, ge=0, le=1)
    table_confidence: Optional[float] = Field(None, ge=0, le=1)
    ocr_char_confidence: Optional[float] = Field(None, ge=0, le=1)


class ReconciliationResult(BaseModel):
    """Result of reconciliation checks."""
    passed: bool = Field(..., description="Overall pass/fail")
    checks: List[Dict[str, Any]] = Field(default_factory=list, description="Individual check results")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    # Specific checks
    balance_check: Optional[bool] = None
    date_sequence_check: Optional[bool] = None
    period_consistency_check: Optional[bool] = None
    totals_sanity_check: Optional[bool] = None


class ConfidenceScore(BaseModel):
    """Confidence scoring breakdown."""
    overall: float = Field(..., ge=0, le=1, description="Overall confidence score")
    needs_review: bool = Field(..., description="Flagged for manual review")
    
    # Component scores
    extraction_score: float = Field(..., ge=0, le=1)
    normalization_score: float = Field(..., ge=0, le=1)
    reconciliation_score: float = Field(..., ge=0, le=1)
    
    # Factors
    factors: Dict[str, float] = Field(default_factory=dict, description="Individual scoring factors")
    penalties: List[str] = Field(default_factory=list, description="Applied penalties")


class VendorNormalization(BaseModel):
    """Vendor normalization result."""
    original: str = Field(..., description="Original vendor name")
    normalized: str = Field(..., description="Normalized vendor name")
    confidence: float = Field(..., ge=0, le=1, description="Normalization confidence")
    rule_id: Optional[UUID] = Field(None, description="Rule ID if matched")
    method: str = Field(..., description="Normalization method")


class FileMetadata(BaseModel):
    """Metadata about uploaded file."""
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    pages: Optional[int] = None
    
    # Sniffed information
    detected_type: Optional[str] = None
    encoding: Optional[str] = None
    has_password: Optional[bool] = None
    malware_scan_result: Optional[str] = None


class BulkIngestionRequest(BaseModel):
    """Request to ingest multiple files."""
    tenant_id: UUID
    files: List[str] = Field(..., description="List of file paths or URLs")
    account_hint: Optional[str] = None
    force_reprocess: bool = False


class BulkIngestionResponse(BaseModel):
    """Response from bulk ingestion."""
    total_files: int
    successful: int
    failed: int
    results: List[IngestionResponse]
    errors: List[Dict[str, Any]]


class IngestionStats(BaseModel):
    """Aggregated ingestion statistics."""
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    
    total_files: int
    total_transactions: int
    total_duplicates: int
    
    avg_confidence: float
    avg_processing_time_ms: float
    
    files_by_type: Dict[str, int]
    files_by_status: Dict[str, int]
    
    top_errors: List[Dict[str, Any]]


class TemplateMatch(BaseModel):
    """Bank template match result."""
    bank_name: str
    template_id: str
    confidence: float = Field(..., ge=0, le=1)
    matched_headers: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)



