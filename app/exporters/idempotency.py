"""
Journal Entry Idempotency Helpers.

Ensures that duplicate export requests are handled safely:
- Compute deterministic hash from JE payload
- Check if hash exists in je_idempotency table
- Return existing vendor reference if duplicate detected
- Store hash + vendor reference on first successful export
"""

import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import JEIdempotencyDB


def compute_je_hash(
    tenant_id: str,
    entries: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compute deterministic SHA-256 hash for journal entry payload.
    
    Hash is based on:
    - tenant_id
    - sorted list of entry lines (account, debit, credit, description)
    - optional metadata (e.g., statement_id, date_range)
    
    Args:
        tenant_id: Tenant identifier
        entries: List of JE lines with {account, debit, credit, description, ...}
        metadata: Optional metadata dict (e.g., source file, date range)
        
    Returns:
        64-character hex string (SHA-256)
        
    Example:
        >>> compute_je_hash(
        ...     tenant_id="tenant_123",
        ...     entries=[
        ...         {"account": "1000", "debit": 100.00, "credit": 0},
        ...         {"account": "4000", "debit": 0, "credit": 100.00}
        ...     ]
        ... )
        'a1b2c3d4...'
    """
    
    # Normalize entries for hashing
    normalized_entries = []
    for entry in entries:
        normalized_entry = {
            "account": str(entry.get("account", "")),
            "debit": round(float(entry.get("debit", 0)), 2),
            "credit": round(float(entry.get("credit", 0)), 2),
            "description": str(entry.get("description", "")).strip(),
            # Include entity/class if present for better uniqueness
            "entity": str(entry.get("entity", "")),
            "class": str(entry.get("class", ""))
        }
        normalized_entries.append(normalized_entry)
    
    # Sort entries by account + debit + credit for deterministic order
    normalized_entries.sort(key=lambda x: (x["account"], x["debit"], x["credit"]))
    
    # Build hash payload
    hash_payload = {
        "tenant_id": tenant_id,
        "entries": normalized_entries,
        "metadata": metadata or {}
    }
    
    # Serialize to JSON (sorted keys for determinism)
    payload_str = json.dumps(hash_payload, sort_keys=True)
    
    # Compute SHA-256
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


def check_idempotency(
    db: Session,
    tenant_id: str,
    payload_hash: str
) -> Optional[str]:
    """
    Check if this JE payload has already been exported.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        payload_hash: Hash from compute_je_hash()
        
    Returns:
        Vendor document ID (e.g., QBO JournalEntry ID) if duplicate detected,
        None if this is a new export
    """
    
    existing = db.query(JEIdempotencyDB).filter(
        JEIdempotencyDB.tenant_id == tenant_id,
        JEIdempotencyDB.payload_hash == payload_hash
    ).first()
    
    if existing:
        return existing.qbo_doc_id
    
    return None


def store_idempotency(
    db: Session,
    tenant_id: str,
    payload_hash: str,
    vendor_doc_id: str
) -> JEIdempotencyDB:
    """
    Store idempotency record after successful export.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        payload_hash: Hash from compute_je_hash()
        vendor_doc_id: Vendor-assigned document ID (e.g., QBO JournalEntry ID)
        
    Returns:
        Created JEIdempotencyDB record
        
    Raises:
        IntegrityError: If duplicate hash detected (race condition)
    """
    
    record = JEIdempotencyDB(
        tenant_id=tenant_id,
        payload_hash=payload_hash,
        qbo_doc_id=vendor_doc_id,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        # Race condition: another request stored the same hash
        db.rollback()
        # Re-fetch and return existing record
        existing = db.query(JEIdempotencyDB).filter(
            JEIdempotencyDB.tenant_id == tenant_id,
            JEIdempotencyDB.payload_hash == payload_hash
        ).first()
        
        if not existing:
            # Should never happen, but handle gracefully
            raise RuntimeError(
                f"Idempotency check failed: hash {payload_hash[:8]}... "
                "exists but could not be retrieved"
            )
        
        return existing


def get_or_export(
    db: Session,
    tenant_id: str,
    entries: List[Dict[str, Any]],
    export_fn: callable,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Idempotent export wrapper.
    
    Checks idempotency before calling export function.
    If duplicate detected, returns cached vendor reference.
    If new export, calls export_fn and stores result.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier
        entries: List of JE lines
        export_fn: Function to call for actual export
                   Must return dict with "vendor_doc_id" key
        metadata: Optional metadata for hash computation
        
    Returns:
        Dict with:
        - vendor_doc_id: Vendor document ID
        - is_duplicate: True if this was a duplicate request
        - hash: Payload hash
        
    Example:
        >>> def my_export_to_qbo(tenant_id, entries):
        ...     # Call QBO API
        ...     response = qbo_client.create_journal_entry(...)
        ...     return {"vendor_doc_id": response["Id"]}
        ...
        >>> result = get_or_export(
        ...     db=db,
        ...     tenant_id="tenant_123",
        ...     entries=[...],
        ...     export_fn=lambda: my_export_to_qbo("tenant_123", [...])
        ... )
        >>> print(result["vendor_doc_id"])  # QBO JournalEntry ID
        >>> print(result["is_duplicate"])   # False (first time)
    """
    
    # Compute hash
    payload_hash = compute_je_hash(tenant_id, entries, metadata)
    
    # Check idempotency
    existing_doc_id = check_idempotency(db, tenant_id, payload_hash)
    
    if existing_doc_id:
        # Duplicate detected - return cached result
        return {
            "vendor_doc_id": existing_doc_id,
            "is_duplicate": True,
            "hash": payload_hash,
            "message": "Duplicate export detected - returning existing reference"
        }
    
    # New export - call export function
    export_result = export_fn()
    
    if not isinstance(export_result, dict) or "vendor_doc_id" not in export_result:
        raise ValueError(
            "export_fn must return dict with 'vendor_doc_id' key. "
            f"Got: {export_result}"
        )
    
    vendor_doc_id = export_result["vendor_doc_id"]
    
    # Store idempotency record
    store_idempotency(db, tenant_id, payload_hash, vendor_doc_id)
    
    return {
        "vendor_doc_id": vendor_doc_id,
        "is_duplicate": False,
        "hash": payload_hash,
        "message": "New export completed successfully"
    }

