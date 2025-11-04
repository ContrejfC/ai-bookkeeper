"""
MIME Type Detection via Magic Bytes
===================================

Detect file type using magic bytes rather than relying on extensions.
Falls back to multiple methods for reliability.
"""

import os
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import magic libraries (fallback chain)
MAGIC_AVAILABLE = False
FILETYPE_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
    logger.info("python-magic available for MIME detection")
except ImportError:
    logger.warning("python-magic not available, trying filetype")
    try:
        import filetype
        FILETYPE_AVAILABLE = True
        logger.info("filetype library available for MIME detection")
    except ImportError:
        logger.warning("No magic byte libraries available, using basic detection")


# Magic byte signatures for common formats
MAGIC_SIGNATURES = {
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/zip',
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'OFXHEADER': 'application/ofx',
    b'<?xml': 'application/xml',  # Could be OFX in XML format
}


def detect_mime_basic(file_path: str, content: bytes = None) -> str:
    """
    Basic MIME detection using magic byte signatures.
    
    Args:
        file_path: Path to file
        content: File content bytes (if already read)
    
    Returns:
        Detected MIME type or 'application/octet-stream'
    """
    if content is None:
        try:
            with open(file_path, 'rb') as f:
                content = f.read(512)  # Read first 512 bytes
        except Exception as e:
            logger.error(f"Failed to read file for MIME detection: {e}")
            return 'application/octet-stream'
    
    # Check against known signatures
    for signature, mime_type in MAGIC_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    
    # Check for CSV (text-based with common patterns)
    try:
        text = content.decode('utf-8', errors='ignore')[:1000]
        if ',' in text and ('\n' in text or '\r' in text):
            # Simple heuristic: contains commas and newlines
            lines = text.split('\n')[:5]
            if len(lines) > 1 and all(',' in line for line in lines if line.strip()):
                return 'text/csv'
    except Exception:
        pass
    
    # Check for OFX in XML format
    if b'<OFX>' in content[:1000] or b'<ofx>' in content[:1000]:
        return 'application/ofx'
    
    return 'application/octet-stream'


def detect_mime_python_magic(file_path: str) -> str:
    """
    Detect MIME using python-magic library.
    
    Args:
        file_path: Path to file
    
    Returns:
        Detected MIME type
    """
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except Exception as e:
        logger.error(f"python-magic detection failed: {e}")
        return 'application/octet-stream'


def detect_mime_filetype(file_path: str) -> str:
    """
    Detect MIME using filetype library.
    
    Args:
        file_path: Path to file
    
    Returns:
        Detected MIME type
    """
    try:
        kind = filetype.guess(file_path)
        if kind is not None:
            return kind.mime
    except Exception as e:
        logger.error(f"filetype detection failed: {e}")
    
    return 'application/octet-stream'


def detect_mime(file_path: str, content: bytes = None) -> Tuple[str, str]:
    """
    Detect MIME type using best available method.
    
    Tries methods in order:
    1. python-magic (if available)
    2. filetype (if available)
    3. Basic signature detection
    
    Args:
        file_path: Path to file
        content: Optional file content bytes
    
    Returns:
        Tuple of (mime_type, detection_method)
    """
    # Try python-magic first (most reliable)
    if MAGIC_AVAILABLE:
        try:
            mime_type = detect_mime_python_magic(file_path)
            if mime_type != 'application/octet-stream':
                logger.debug(f"Detected {mime_type} using python-magic")
                return mime_type, "python-magic"
        except Exception as e:
            logger.warning(f"python-magic failed: {e}")
    
    # Try filetype library
    if FILETYPE_AVAILABLE:
        try:
            mime_type = detect_mime_filetype(file_path)
            if mime_type != 'application/octet-stream':
                logger.debug(f"Detected {mime_type} using filetype")
                return mime_type, "filetype"
        except Exception as e:
            logger.warning(f"filetype failed: {e}")
    
    # Fall back to basic detection
    mime_type = detect_mime_basic(file_path, content)
    logger.debug(f"Detected {mime_type} using basic signatures")
    return mime_type, "basic"


def is_text_file(file_path: str, sample_size: int = 8192) -> bool:
    """
    Check if file appears to be text-based.
    
    Args:
        file_path: Path to file
        sample_size: Number of bytes to sample
    
    Returns:
        True if file appears to be text
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        
        # Check for null bytes (strong indicator of binary)
        if b'\x00' in sample:
            return False
        
        # Try to decode as UTF-8
        try:
            sample.decode('utf-8')
            return True
        except UnicodeDecodeError:
            pass
        
        # Try common encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                sample.decode(encoding)
                return True
            except UnicodeDecodeError:
                continue
        
        return False
    except Exception as e:
        logger.error(f"Failed to check if text file: {e}")
        return False


def detect_encoding(file_path: str, sample_size: int = 8192) -> Optional[str]:
    """
    Detect text file encoding.
    
    Args:
        file_path: Path to file
        sample_size: Number of bytes to sample
    
    Returns:
        Detected encoding or None
    """
    try:
        import chardet
        
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
        
        result = chardet.detect(sample)
        if result['confidence'] > 0.7:
            return result['encoding']
    except ImportError:
        logger.debug("chardet not available for encoding detection")
    except Exception as e:
        logger.error(f"Encoding detection failed: {e}")
    
    # Fallback: try common encodings
    with open(file_path, 'rb') as f:
        sample = f.read(sample_size)
    
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    
    return None


def get_file_info(file_path: str) -> dict:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to file
    
    Returns:
        Dictionary with file metadata
    """
    stat = os.stat(file_path)
    mime_type, detection_method = detect_mime(file_path)
    
    info = {
        'filename': os.path.basename(file_path),
        'size_bytes': stat.st_size,
        'mime_type': mime_type,
        'detection_method': detection_method,
        'is_text': is_text_file(file_path),
    }
    
    if info['is_text']:
        info['encoding'] = detect_encoding(file_path)
    
    return info



