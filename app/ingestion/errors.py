"""
Ingestion Error Taxonomy
========================

Stable error codes with HTTP status mapping, hints, and evidence capture.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class IngestionError(HTTPException):
    """Base exception for ingestion errors with stable codes."""
    
    def __init__(
        self,
        code: str,
        status_code: int,
        detail: str,
        hint: Optional[str] = None,
        where: Optional[str] = None,
        evidence_sample: Optional[str] = None,
        **kwargs
    ):
        self.code = code
        self.hint = hint
        self.where = where
        self.evidence_sample = evidence_sample
        
        error_detail = {
            "code": code,
            "message": detail,
            "hint": hint,
            "where": where,
            "evidence_sample": evidence_sample,
            **kwargs
        }
        
        super().__init__(status_code=status_code, detail=error_detail)


# ============================================================================
# 400 - Bad Request Errors
# ============================================================================

class ZipUnsupportedContentsError(IngestionError):
    """ZIP archive contains unsupported file types."""
    
    def __init__(self, unsupported_files: list, **kwargs):
        super().__init__(
            code="400_ZIP_UNSUPPORTED_CONTENTS",
            status_code=400,
            detail="ZIP archive contains unsupported file types",
            hint="ZIP files must only contain CSV, OFX, PDF, or image files",
            where="zip_extraction",
            evidence_sample=f"Found: {', '.join(unsupported_files[:3])}",
            **kwargs
        )


class InvalidFileFormatError(IngestionError):
    """File format is invalid or corrupted."""
    
    def __init__(self, file_type: str, reason: str, **kwargs):
        super().__init__(
            code="400_INVALID_FILE_FORMAT",
            status_code=400,
            detail=f"Invalid {file_type} format: {reason}",
            hint=f"Ensure the {file_type} file is not corrupted",
            where=f"{file_type}_parsing",
            **kwargs
        )


# ============================================================================
# 413 - Payload Too Large
# ============================================================================

class FileTooLargeError(IngestionError):
    """File exceeds size limits."""
    
    def __init__(self, file_type: str, size_mb: float, limit_mb: float, **kwargs):
        super().__init__(
            code="413_FILE_TOO_LARGE",
            status_code=413,
            detail=f"File size {size_mb:.1f}MB exceeds {file_type} limit of {limit_mb:.1f}MB",
            hint=f"Split the file into smaller chunks or contact support for enterprise limits",
            where="size_check",
            evidence_sample=f"Size: {size_mb:.1f}MB, Limit: {limit_mb:.1f}MB",
            **kwargs
        )


class TooManyRowsError(IngestionError):
    """File contains too many rows."""
    
    def __init__(self, row_count: int, limit: int, **kwargs):
        super().__init__(
            code="413_TOO_MANY_ROWS",
            status_code=413,
            detail=f"File contains {row_count} rows, exceeds limit of {limit}",
            hint="Split the file into smaller batches",
            where="row_count_check",
            evidence_sample=f"Rows: {row_count}, Limit: {limit}",
            **kwargs
        )


# ============================================================================
# 415 - Unsupported Media Type
# ============================================================================

class UnsupportedMediaTypeError(IngestionError):
    """File type is not supported."""
    
    def __init__(self, mime_type: str, filename: str, **kwargs):
        super().__init__(
            code="415_UNSUPPORTED_MEDIA_TYPE",
            status_code=415,
            detail=f"Unsupported file type: {mime_type}",
            hint="Supported types: CSV, OFX/QFX, PDF, JPEG, PNG, ZIP",
            where="mime_check",
            evidence_sample=f"File: {filename}, MIME: {mime_type}",
            **kwargs
        )


# ============================================================================
# 422 - Unprocessable Entity (Parsing/Extraction Errors)
# ============================================================================

class FileEncryptedError(IngestionError):
    """File is password-protected."""
    
    def __init__(self, file_type: str = "PDF", **kwargs):
        super().__init__(
            code="422_FILE_ENCRYPTED",
            status_code=422,
            detail=f"{file_type} file is password-protected",
            hint="Remove password protection or provide an unencrypted version",
            where="password_check",
            **kwargs
        )


class ParseFailedError(IngestionError):
    """Failed to parse file contents."""
    
    def __init__(self, file_type: str, reason: str, **kwargs):
        super().__init__(
            code="422_PARSE_FAILED",
            status_code=422,
            detail=f"Failed to parse {file_type}: {reason}",
            hint="Check file format and encoding",
            where=f"{file_type}_parsing",
            evidence_sample=reason[:200] if reason else None,
            **kwargs
        )


class TableNotFoundError(IngestionError):
    """Could not detect transaction table in file."""
    
    def __init__(self, extraction_methods_tried: list, **kwargs):
        super().__init__(
            code="422_TABLE_NOT_FOUND",
            status_code=422,
            detail="Could not detect transaction table in document",
            hint="Ensure the document contains a clear transaction table with headers",
            where="table_detection",
            evidence_sample=f"Tried: {', '.join(extraction_methods_tried)}",
            **kwargs
        )


class LocaleAmbiguousError(IngestionError):
    """Date or number format is ambiguous."""
    
    def __init__(self, field: str, samples: list, **kwargs):
        super().__init__(
            code="422_LOCALE_AMBIGUOUS",
            status_code=422,
            detail=f"Ambiguous {field} format detected",
            hint=f"Standardize {field} format (e.g., YYYY-MM-DD for dates, use clear decimal separators)",
            where="locale_detection",
            evidence_sample=f"Samples: {samples[:3]}",
            **kwargs
        )


class AmountPolarityUnknownError(IngestionError):
    """Cannot determine if amounts are debits or credits."""
    
    def __init__(self, **kwargs):
        super().__init__(
            code="422_AMOUNT_POLARITY_UNKNOWN",
            status_code=422,
            detail="Cannot determine transaction polarity (debit/credit)",
            hint="Ensure amounts have clear positive/negative signs or separate debit/credit columns",
            where="amount_normalization",
            **kwargs
        )


class MalwareSuspectedError(IngestionError):
    """File appears to contain malware."""
    
    def __init__(self, scan_result: str, **kwargs):
        super().__init__(
            code="422_MALWARE_SUSPECTED",
            status_code=422,
            detail="File flagged by malware scanner",
            hint="Scan the file with antivirus software before uploading",
            where="malware_scan",
            evidence_sample=scan_result[:100],
            **kwargs
        )


class ReconciliationFailedError(IngestionError):
    """Reconciliation checks failed."""
    
    def __init__(self, failures: list, **kwargs):
        super().__init__(
            code="422_RECONCILIATION_FAILED",
            status_code=422,
            detail="Transaction reconciliation failed",
            hint="Check for missing transactions, incorrect balances, or data inconsistencies",
            where="reconciliation",
            evidence_sample=f"Failures: {'; '.join(failures[:3])}",
            **kwargs
        )


class MissingRequiredFieldError(IngestionError):
    """Required field is missing from the data."""
    
    def __init__(self, field_name: str, **kwargs):
        super().__init__(
            code="422_MISSING_REQUIRED_FIELD",
            status_code=422,
            detail=f"Required field '{field_name}' not found",
            hint=f"Ensure the file contains a '{field_name}' column or field",
            where="field_mapping",
            **kwargs
        )


class InvalidDataFormatError(IngestionError):
    """Data format is invalid."""
    
    def __init__(self, field: str, value: str, expected: str, **kwargs):
        super().__init__(
            code="422_INVALID_DATA_FORMAT",
            status_code=422,
            detail=f"Invalid format for {field}: expected {expected}",
            hint=f"Correct the {field} format",
            where="data_validation",
            evidence_sample=f"Value: {value}, Expected: {expected}",
            **kwargs
        )


# ============================================================================
# 500 - Internal Server Errors
# ============================================================================

class ExtractionTimeoutError(IngestionError):
    """Extraction took too long."""
    
    def __init__(self, timeout_seconds: int, **kwargs):
        super().__init__(
            code="500_EXTRACTION_TIMEOUT",
            status_code=500,
            detail=f"Extraction exceeded timeout of {timeout_seconds}s",
            hint="Try a smaller file or contact support",
            where="extraction",
            **kwargs
        )


class InternalProcessingError(IngestionError):
    """Unexpected internal error."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            code="500_INTERNAL_ERROR",
            status_code=500,
            detail=f"Internal processing error: {message}",
            hint="Contact support if this persists",
            where="pipeline",
            **kwargs
        )


# ============================================================================
# Error Code Mapping
# ============================================================================

ERROR_CODE_MAP: Dict[str, type[IngestionError]] = {
    "400_ZIP_UNSUPPORTED_CONTENTS": ZipUnsupportedContentsError,
    "400_INVALID_FILE_FORMAT": InvalidFileFormatError,
    "413_FILE_TOO_LARGE": FileTooLargeError,
    "413_TOO_MANY_ROWS": TooManyRowsError,
    "415_UNSUPPORTED_MEDIA_TYPE": UnsupportedMediaTypeError,
    "422_FILE_ENCRYPTED": FileEncryptedError,
    "422_PARSE_FAILED": ParseFailedError,
    "422_TABLE_NOT_FOUND": TableNotFoundError,
    "422_LOCALE_AMBIGUOUS": LocaleAmbiguousError,
    "422_AMOUNT_POLARITY_UNKNOWN": AmountPolarityUnknownError,
    "422_MALWARE_SUSPECTED": MalwareSuspectedError,
    "422_RECONCILIATION_FAILED": ReconciliationFailedError,
    "422_MISSING_REQUIRED_FIELD": MissingRequiredFieldError,
    "422_INVALID_DATA_FORMAT": InvalidDataFormatError,
    "500_EXTRACTION_TIMEOUT": ExtractionTimeoutError,
    "500_INTERNAL_ERROR": InternalProcessingError,
}


def get_error_by_code(code: str) -> Optional[type[IngestionError]]:
    """Get error class by stable code."""
    return ERROR_CODE_MAP.get(code)



