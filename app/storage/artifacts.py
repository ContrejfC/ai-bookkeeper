"""
Artifact storage abstraction - Local disk or S3.

Environment variables:
- S3_BUCKET: If set, use S3; otherwise use local disk
- S3_ENDPOINT: S3-compatible endpoint (optional)
- S3_ACCESS_KEY_ID: AWS access key
- S3_SECRET_ACCESS_KEY: AWS secret key
"""
import os
import logging
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Check if S3 is configured
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")

USE_S3 = bool(S3_BUCKET and S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY)


def _get_s3_client():
    """Get boto3 S3 client (lazy import)."""
    try:
        import boto3
        
        session = boto3.Session(
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY
        )
        
        client_kwargs = {}
        if S3_ENDPOINT:
            client_kwargs['endpoint_url'] = S3_ENDPOINT
        
        return session.client('s3', **client_kwargs)
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        raise
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise


def write_artifact(path: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Write artifact to storage (local or S3).
    
    Args:
        path: Relative path (e.g., "reports/analytics/daily_2025-10-11.json")
        content: Binary content
        content_type: MIME type
    
    Returns:
        Full path or S3 URL
    """
    if USE_S3:
        # Write to S3
        s3_client = _get_s3_client()
        s3_key = path
        
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=content,
                ContentType=content_type
            )
            
            s3_url = f"s3://{S3_BUCKET}/{s3_key}"
            logger.info(f"Wrote artifact to S3: {s3_url}")
            return s3_url
        
        except Exception as e:
            logger.error(f"Failed to write to S3: {e}")
            # Fall back to local disk
            logger.warning("Falling back to local disk")
    
    # Write to local disk
    local_path = Path(path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(local_path, 'wb') as f:
        f.write(content)
    
    logger.debug(f"Wrote artifact to local disk: {local_path}")
    return str(local_path.absolute())


def read_artifact(path: str) -> Optional[bytes]:
    """
    Read artifact from storage (local or S3).
    
    Args:
        path: Relative path or s3:// URL
    
    Returns:
        Binary content or None if not found
    """
    if path.startswith("s3://"):
        # Read from S3
        s3_client = _get_s3_client()
        
        # Parse s3://bucket/key
        path_parts = path[5:].split("/", 1)
        bucket = path_parts[0]
        key = path_parts[1] if len(path_parts) > 1 else ""
        
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        
        except s3_client.exceptions.NoSuchKey:
            logger.warning(f"S3 object not found: {path}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to read from S3: {e}")
            return None
    
    else:
        # Read from local disk
        local_path = Path(path)
        
        if not local_path.exists():
            logger.warning(f"Local file not found: {path}")
            return None
        
        with open(local_path, 'rb') as f:
            return f.read()


def get_presigned_url(path: str, expiration: int = 3600) -> Optional[str]:
    """
    Get presigned URL for artifact (S3 only).
    
    Args:
        path: Relative path or s3:// URL
        expiration: URL expiration in seconds (default 1 hour)
    
    Returns:
        Presigned URL or None if not S3
    """
    if not USE_S3:
        return None
    
    s3_client = _get_s3_client()
    
    # Parse path
    if path.startswith("s3://"):
        path_parts = path[5:].split("/", 1)
        bucket = path_parts[0]
        key = path_parts[1] if len(path_parts) > 1 else ""
    else:
        bucket = S3_BUCKET
        key = path
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        
        logger.debug(f"Generated presigned URL for {path}")
        return url
    
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None


def list_artifacts(prefix: str = "") -> list:
    """
    List artifacts with given prefix.
    
    Args:
        prefix: Path prefix (e.g., "reports/analytics/")
    
    Returns:
        List of paths
    """
    if USE_S3:
        # List from S3
        s3_client = _get_s3_client()
        
        try:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [f"s3://{S3_BUCKET}/{obj['Key']}" for obj in response['Contents']]
        
        except Exception as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []
    
    else:
        # List from local disk
        local_prefix = Path(prefix)
        
        if not local_prefix.exists():
            return []
        
        if local_prefix.is_file():
            return [str(local_prefix.absolute())]
        
        return [str(p.absolute()) for p in local_prefix.rglob("*") if p.is_file()]


def delete_artifact(path: str) -> bool:
    """
    Delete artifact from storage.
    
    Args:
        path: Relative path or s3:// URL
    
    Returns:
        True if deleted, False otherwise
    """
    if path.startswith("s3://"):
        # Delete from S3
        s3_client = _get_s3_client()
        
        path_parts = path[5:].split("/", 1)
        bucket = path_parts[0]
        key = path_parts[1] if len(path_parts) > 1 else ""
        
        try:
            s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted S3 object: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete S3 object: {e}")
            return False
    
    else:
        # Delete from local disk
        local_path = Path(path)
        
        if not local_path.exists():
            return False
        
        try:
            local_path.unlink()
            logger.debug(f"Deleted local file: {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete local file: {e}")
            return False


# Convenience functions for specific artifact types

def write_report(filename: str, content: bytes) -> str:
    """Write analytics report (JSON)."""
    return write_artifact(f"reports/analytics/{filename}", content, "application/json")


def write_receipt(filename: str, content: bytes) -> str:
    """Write receipt (PDF or image)."""
    content_type = "application/pdf" if filename.endswith(".pdf") else "image/jpeg"
    return write_artifact(f"artifacts/receipts/{filename}", content, content_type)


def write_export(filename: str, content: bytes) -> str:
    """Write export (CSV)."""
    return write_artifact(f"exports/{filename}", content, "text/csv")


def get_storage_info() -> dict:
    """Get storage configuration info."""
    return {
        "backend": "s3" if USE_S3 else "local",
        "s3_bucket": S3_BUCKET if USE_S3 else None,
        "s3_endpoint": S3_ENDPOINT if USE_S3 else None,
        "local_base": str(Path.cwd()) if not USE_S3 else None
    }

