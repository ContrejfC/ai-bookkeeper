"""
Ingestion Database Models
=========================

SQLAlchemy models for statement files, transactions, artifacts, and metrics.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, BigInteger, DateTime, Text, Float,
    ForeignKey, Index, UniqueConstraint, Boolean, JSON, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.db.base_class import Base


class FileStatus(str, enum.Enum):
    """Status of file processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class SourceType(str, enum.Enum):
    """Source type for transactions."""
    CSV = "csv"
    OFX = "ofx"
    PDF = "pdf"
    OCR = "ocr"
    IMAGE = "image"


class StatementFile(Base):
    """
    Uploaded statement files with metadata.
    
    Tracks file ingestion status, size, pages, and processing metadata.
    """
    __tablename__ = "statement_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # File identification
    sha256 = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    
    # Source and processing info
    source = Column(Enum(SourceType), nullable=False)
    status = Column(Enum(FileStatus), nullable=False, default=FileStatus.PENDING)
    
    # Document structure
    pages = Column(Integer, nullable=True)  # Total pages (PDF/multi-page docs)
    ocr_pages = Column(Integer, nullable=True)  # Pages that required OCR
    
    # Processing metadata
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="file", cascade="all, delete-orphan")
    artifacts = relationship("IngestionArtifact", back_populates="file", cascade="all, delete-orphan")
    metrics = relationship("IngestionMetric", back_populates="file", uselist=False, cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_statement_files_tenant_sha256', 'tenant_id', 'sha256'),
        Index('ix_statement_files_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_statement_files_status', 'status'),
    )


class Transaction(Base):
    """
    Normalized transaction records extracted from statements.
    
    Canonical schema with deduplication support via fingerprints.
    """
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("statement_files.id"), nullable=False, index=True)
    
    # Account information
    account_id = Column(String(100), nullable=False, index=True)  # Account number or identifier
    
    # Transaction dates
    post_date = Column(DateTime, nullable=False, index=True)  # Posting date
    value_date = Column(DateTime, nullable=True)  # Value/effective date
    
    # Transaction details
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)  # Signed amount (negative = debit, positive = credit)
    balance = Column(Float, nullable=True)  # Running balance after transaction
    currency = Column(String(3), nullable=False, default="USD")  # ISO 4217
    
    # Source metadata
    source = Column(Enum(SourceType), nullable=False)
    source_confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Deduplication
    fingerprint = Column(String(64), nullable=False, index=True)  # SHA-1 hash for dedup
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True)
    
    # Flags
    needs_review = Column(Boolean, nullable=False, default=False)
    reconciliation_passed = Column(Boolean, nullable=False, default=True)
    
    # Raw data (JSON)
    raw_data = Column(JSON, nullable=True)  # Original row data
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    file = relationship("StatementFile", back_populates="transactions")
    
    # Indexes and constraints
    __table_args__ = (
        Index('ix_transactions_tenant_fingerprint', 'tenant_id', 'fingerprint'),
        Index('ix_transactions_tenant_post_date', 'tenant_id', 'post_date'),
        Index('ix_transactions_tenant_account', 'tenant_id', 'account_id'),
        Index('ix_transactions_needs_review', 'needs_review'),
        UniqueConstraint('tenant_id', 'fingerprint', name='uq_tenant_fingerprint'),
    )


class IngestionArtifact(Base):
    """
    Artifacts generated during ingestion (samples, metadata, debug info).
    
    Stores sample rows, header detection results, and OCR outputs.
    """
    __tablename__ = "ingestion_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("statement_files.id"), nullable=False, index=True)
    
    # Artifact metadata
    kind = Column(String(50), nullable=False)  # e.g., "sample_rows", "header_detection", "ocr_output"
    path = Column(String(500), nullable=True)  # File path if saved to disk
    meta_json = Column(JSON, nullable=False)  # Artifact data/metadata
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    file = relationship("StatementFile", back_populates="artifacts")
    
    # Indexes
    __table_args__ = (
        Index('ix_ingestion_artifacts_file_kind', 'file_id', 'kind'),
    )


class VendorRule(Base):
    """
    Vendor normalization rules (tenant-specific and global).
    
    Maps vendor name patterns to normalized names.
    """
    __tablename__ = "vendor_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # NULL = global rule
    
    # Rule definition
    pattern = Column(String(255), nullable=False)  # Regex or exact match
    normalized = Column(String(255), nullable=False)  # Normalized vendor name
    is_regex = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=100)  # Lower = higher priority
    
    # Metadata
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_vendor_rules_tenant_active', 'tenant_id', 'active'),
        Index('ix_vendor_rules_pattern', 'pattern'),
    )


class IngestionMetric(Base):
    """
    Ingestion performance and quality metrics per file.
    
    Tracks processing time, row counts, confidence, and reconciliation status.
    """
    __tablename__ = "ingestion_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("statement_files.id"), nullable=False, unique=True, index=True)
    
    # Performance metrics
    parse_time_ms = Column(Integer, nullable=False)  # Total processing time
    extraction_time_ms = Column(Integer, nullable=True)  # Extraction phase time
    normalization_time_ms = Column(Integer, nullable=True)  # Normalization phase time
    
    # Output metrics
    rows_in = Column(Integer, nullable=False)  # Raw rows extracted
    rows_out = Column(Integer, nullable=False)  # Valid transactions after filtering
    rows_duplicates = Column(Integer, nullable=False, default=0)  # Duplicate count
    
    # Quality metrics
    confidence_avg = Column(Float, nullable=False)  # Average confidence score
    confidence_min = Column(Float, nullable=False)  # Minimum confidence
    needs_review_count = Column(Integer, nullable=False, default=0)  # Count flagged for review
    
    # Reconciliation
    reconciliation_passed = Column(Boolean, nullable=False)
    reconciliation_errors = Column(JSON, nullable=True)  # List of reconciliation failures
    
    # Extraction path used
    extraction_method = Column(String(50), nullable=True)  # e.g., "pdf_text", "ocr_grid", "csv"
    
    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    file = relationship("StatementFile", back_populates="metrics")
    
    # Indexes
    __table_args__ = (
        Index('ix_ingestion_metrics_created', 'created_at'),
        Index('ix_ingestion_metrics_confidence', 'confidence_avg'),
    )



