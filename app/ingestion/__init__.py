"""
AI-Bookkeeper Ingestion Pipeline
=================================

Robust bank statement ingestion with multi-format support, OCR fallbacks,
reconciliation, deduplication, and confidence scoring.

Supported formats:
- CSV (various encodings and delimiters)
- OFX/QFX (Open Financial Exchange)
- PDF (text extraction with OCR fallback)
- Images (JPEG/PNG with OCR)
- ZIP archives (recursive processing)

Features:
- MIME type detection via magic bytes
- Size limits and malware scanning
- Password-protected PDF detection
- Multi-strategy extraction with fallbacks
- Automatic reconciliation and balance validation
- Duplicate detection across uploads
- Confidence scoring with review flagging
- PII redaction in logs and artifacts
- Comprehensive error taxonomy
"""

__version__ = "1.0.0"

# from app.ingestion.pipeline import IngestionPipeline  # TODO: Uncomment when pipeline is implemented
from app.ingestion.errors import IngestionError
from app.ingestion.schemas import CanonicalTransaction, IngestionRequest, IngestionResponse

__all__ = [
    # "IngestionPipeline",  # TODO: Uncomment when pipeline is implemented
    "IngestionError",
    "CanonicalTransaction",
    "IngestionRequest",
    "IngestionResponse",
]

