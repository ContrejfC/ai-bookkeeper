"""
QuickBooks Online Service Layer
================================

This service provides:
- OAuth token management (storage, refresh)
- Idempotent journal entry posting
- Balance validation
- Demo/mock export support

Key Features:
------------
1. **Token Management**
   - Stores OAuth tokens per tenant
   - Auto-refreshes expired tokens (5-min buffer)
   - Handles token expiration gracefully

2. **Idempotent Posting**
   - Computes payload hash for deduplication
   - Checks if JE already posted before API call
   - Returns existing QBO doc ID if duplicate

3. **Demo Mode Support**
   - When DEMO_MODE=true, returns mock data
   - No actual QBO API calls made
   - Useful for demos and testing

4. **Audit Logging**
   - Logs all QBO connections
   - Logs all JE posts (success/failure)
   - Tracks payload hashes for debugging

Usage:
------
```python
from app.services.qbo import QBOService

service = QBOService(db)

# Store OAuth tokens after callback
service.store_tokens(tenant_id, realm_id, access_token, refresh_token, expires_at)

# Post journal entry with idempotency
result = await service.post_idempotent_je(tenant_id, payload)
# Returns: { "qbo_doc_id": "123", "idempotent": False, ... }
```
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import QBOTokenDB, JEIdempotencyDB, DecisionAuditLogDB
from app.integrations.qbo.client import QBOClient, DEMO_MODE, QBO_ENV

logger = logging.getLogger(__name__)


class QBOService:
    """Service for QuickBooks Online integration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = QBOClient()
    
    def store_tokens(
        self,
        tenant_id: str,
        realm_id: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime
    ):
        """Store OAuth tokens for tenant."""
        
        # Check for existing tokens
        existing = self.db.query(QBOTokenDB).filter(
            QBOTokenDB.tenant_id == tenant_id
        ).first()
        
        if existing:
            # Update existing
            existing.realm_id = realm_id
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.expires_at = expires_at
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            token = QBOTokenDB(
                tenant_id=tenant_id,
                realm_id=realm_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                scope="com.intuit.quickbooks.accounting"
            )
            self.db.add(token)
        
        self.db.commit()
        
        # Audit log
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            action="QBO_CONNECTED"
        )
        self.db.add(audit)
        self.db.commit()
        
        logger.info(f"QBO tokens stored for tenant {tenant_id}, realm {realm_id[:8]}***")
    
    async def get_fresh_token(self, tenant_id: str) -> Tuple[str, str]:
        """
        Get fresh access token for tenant, refreshing if necessary.
        
        Returns:
            (access_token, realm_id)
        
        Raises:
            Exception if no tokens or refresh fails
        """
        token_record = self.db.query(QBOTokenDB).filter(
            QBOTokenDB.tenant_id == tenant_id
        ).first()
        
        if not token_record:
            raise Exception("QBO_NOT_CONNECTED")
        
        # Check if token is expired or expiring soon (5 min buffer)
        if token_record.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            # Refresh token
            try:
                new_tokens = await self.client.refresh_tokens(token_record.refresh_token)
                
                # Update stored tokens
                token_record.access_token = new_tokens["access_token"]
                token_record.refresh_token = new_tokens["refresh_token"]
                token_record.expires_at = new_tokens["expires_at"]
                token_record.updated_at = datetime.utcnow()
                self.db.commit()
                
                # Audit log
                audit = DecisionAuditLogDB(
                    timestamp=datetime.utcnow(),
                    tenant_id=tenant_id,
                    action="QBO_TOKEN_REFRESHED"
                )
                self.db.add(audit)
                self.db.commit()
                
                logger.info(f"QBO token refreshed for tenant {tenant_id}")
                
            except Exception as e:
                logger.error(f"QBO token refresh failed for tenant {tenant_id}: {e}")
                raise
        
        return token_record.access_token, token_record.realm_id
    
    def normalize_je_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize journal entry payload for deterministic hashing.
        
        Rules:
        - Sort lines by amount then accountRef
        - Round amounts to 2 decimals
        - Strip whitespace
        - Ordered keys
        
        Args:
            payload: Raw JE payload
        
        Returns:
            Normalized payload
        """
        normalized = {
            "txnDate": payload.get("txnDate", ""),
            "refNumber": (payload.get("refNumber", "") or "").strip(),
            "privateNote": (payload.get("privateNote", "") or "").strip(),
            "lines": []
        }
        
        # Normalize and sort lines
        for line in payload.get("lines", []):
            normalized_line = {
                "amount": round(float(line["amount"]), 2),
                "postingType": line["postingType"],
                "accountRef": {"value": str(line["accountRef"]["value"])}
            }
            normalized["lines"].append(normalized_line)
        
        # Sort lines by amount then account for consistency
        normalized["lines"].sort(key=lambda x: (x["amount"], x["accountRef"]["value"]))
        
        return normalized
    
    def compute_payload_hash(self, tenant_id: str, payload: Dict[str, Any]) -> str:
        """
        Compute deterministic SHA-256 hash of normalized payload.
        
        Args:
            tenant_id: Tenant identifier
            payload: JE payload
        
        Returns:
            64-character hex hash
        """
        # Normalize payload
        normalized = self.normalize_je_payload(payload)
        
        # Create deterministic JSON string
        payload_str = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        
        # Include tenant_id in hash for tenant isolation
        hash_input = f"{tenant_id}:{payload_str}"
        
        # Compute SHA-256
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    async def _post_mock_je(
        self,
        tenant_id: str,
        payload: Dict[str, Any],
        payload_hash: str
    ) -> Dict[str, Any]:
        """
        Post mock journal entry for demo mode.
        
        This method simulates a QBO export without making actual API calls.
        Used when DEMO_MODE=true for testing and demos.
        
        Args:
            tenant_id: Tenant identifier
            payload: JE payload
            payload_hash: Hash of payload for idempotency
        
        Returns:
            Mock response matching real QBO response format
        """
        logger.info(f"[DEMO MODE] Mock JE post for tenant {tenant_id}")
        
        # Check idempotency (same as real mode)
        existing = self.db.query(JEIdempotencyDB).filter(
            JEIdempotencyDB.tenant_id == tenant_id,
            JEIdempotencyDB.payload_hash == payload_hash
        ).first()
        
        if existing:
            # Already "posted" - idempotent response
            logger.info(f"[DEMO MODE] Idempotent mock JE, doc {existing.qbo_doc_id}")
            return {
                "status": 200,
                "qbo_doc_id": existing.qbo_doc_id,
                "idempotent": True,
                "posted_mock": True,
                "message": "Mock journal entry already posted (idempotent)"
            }
        
        # Generate fake QBO doc ID
        import uuid
        qbo_doc_id = f"mock_{uuid.uuid4().hex[:12]}"
        
        # Store idempotency record (so future calls return same ID)
        try:
            idempotency = JEIdempotencyDB(
                tenant_id=tenant_id,
                payload_hash=payload_hash,
                qbo_doc_id=qbo_doc_id,
                qbo_sync_token="MOCK",
                posted_at=datetime.utcnow(),
                payload_json=payload
            )
            self.db.add(idempotency)
            self.db.commit()
        except IntegrityError:
            # Race condition - another request posted the same JE
            self.db.rollback()
            existing = self.db.query(JEIdempotencyDB).filter(
                JEIdempotencyDB.tenant_id == tenant_id,
                JEIdempotencyDB.payload_hash == payload_hash
            ).first()
            
            if existing:
                return {
                    "status": 200,
                    "qbo_doc_id": existing.qbo_doc_id,
                    "idempotent": True,
                    "posted_mock": True,
                    "message": "Mock journal entry already posted (race condition)"
                }
            else:
                raise
        
        # Audit log
        audit = DecisionAuditLogDB(
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            action="QBO_JE_POSTED_MOCK",
            metadata={"qbo_doc_id": qbo_doc_id, "payload_hash": payload_hash[:16]}
        )
        self.db.add(audit)
        self.db.commit()
        
        logger.info(f"[DEMO MODE] Mock JE posted, doc {qbo_doc_id}")
        
        return {
            "status": 201,
            "qbo_doc_id": qbo_doc_id,
            "idempotent": False,
            "posted_mock": True,
            "message": "Mock journal entry posted successfully (DEMO MODE)"
        }
    
    def validate_balance(self, lines: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Validate that debits equal credits.
        
        Args:
            lines: List of JE lines with amount and postingType
        
        Returns:
            (is_valid, error_message)
        """
        total_debit = sum(
            round(float(line["amount"]), 2)
            for line in lines
            if line["postingType"] == "Debit"
        )
        
        total_credit = sum(
            round(float(line["amount"]), 2)
            for line in lines
            if line["postingType"] == "Credit"
        )
        
        # Allow for small floating point differences
        if abs(total_debit - total_credit) > 0.01:
            return False, f"Debits ({total_debit:.2f}) must equal credits ({total_credit:.2f})"
        
        return True, None
    
    async def post_idempotent_je(
        self,
        tenant_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post journal entry to QBO with idempotency.
        
        Supports demo mode for testing without QBO connection.
        
        Args:
            tenant_id: Tenant identifier
            payload: JE payload in simplified format
                {
                    "txnDate": "2025-10-27",
                    "lines": [
                        {"account": "1000", "debit": 100, "credit": 0},
                        {"account": "4000", "debit": 0, "credit": 100}
                    ],
                    "refNumber": "JE-001",
                    "privateNote": "Optional memo"
                }
        
        Returns:
            {
                "status": 201 or 200,
                "qbo_doc_id": str,
                "idempotent": bool,
                "posted_mock": bool (only in demo mode),
                "message": str
            }
        
        Raises:
            ValueError: If journal entry is unbalanced
            Exception: If QBO API call fails
        """
        # Validate balance
        is_balanced, balance_error = self.validate_balance(payload.get("lines", []))
        if not is_balanced:
            raise ValueError(f"UNBALANCED_JE:{balance_error}")
        
        # Compute payload hash for idempotency
        payload_hash = self.compute_payload_hash(tenant_id, payload)
        
        # DEMO MODE: Return mock response without calling QBO API
        if DEMO_MODE:
            return await self._post_mock_je(tenant_id, payload, payload_hash)
        
        # Check idempotency
        existing = self.db.query(JEIdempotencyDB).filter(
            JEIdempotencyDB.tenant_id == tenant_id,
            JEIdempotencyDB.payload_hash == payload_hash
        ).first()
        
        if existing:
            # Already posted - idempotent response
            logger.info(f"Idempotent JE post for tenant {tenant_id}, hash {payload_hash[:16]}***, QBO doc {existing.qbo_doc_id}")
            return {
                "status": 200,
                "qbo_doc_id": existing.qbo_doc_id,
                "idempotent": True,
                "message": "Journal entry already posted (idempotent)"
            }
        
        # Get fresh token
        access_token, realm_id = await self.get_fresh_token(tenant_id)
        
        # Build QBO payload
        qbo_payload = self.client.build_journal_entry_payload(
            txn_date=payload.get("txnDate"),
            lines=payload.get("lines", []),
            ref_number=payload.get("refNumber"),
            private_note=payload.get("privateNote", "AI Bookkeeper")
        )
        
        # Post to QBO
        try:
            result = await self.client.post_journal_entry(realm_id, access_token, qbo_payload)
            qbo_doc_id = result["qbo_doc_id"]
            
            # Store idempotency record
            idempotency = JEIdempotencyDB(
                tenant_id=tenant_id,
                payload_hash=payload_hash,
                qbo_doc_id=qbo_doc_id
            )
            self.db.add(idempotency)
            
            # Audit log
            audit = DecisionAuditLogDB(
                timestamp=datetime.utcnow(),
                tenant_id=tenant_id,
                action="QBO_JE_POSTED"
            )
            self.db.add(audit)
            
            try:
                self.db.commit()
            except IntegrityError:
                # Race condition - another request posted the same JE
                self.db.rollback()
                existing = self.db.query(JEIdempotencyDB).filter(
                    JEIdempotencyDB.tenant_id == tenant_id,
                    JEIdempotencyDB.payload_hash == payload_hash
                ).first()
                
                if existing:
                    return {
                        "status": 200,
                        "qbo_doc_id": existing.qbo_doc_id,
                        "idempotent": True,
                        "message": "Journal entry already posted (race condition)"
                    }
                else:
                    raise
            
            logger.info(f"JE posted to QBO for tenant {tenant_id}, doc {qbo_doc_id}, hash {payload_hash[:16]}***")
            
            return {
                "status": 201,
                "qbo_doc_id": qbo_doc_id,
                "idempotent": False,
                "message": "Journal entry posted successfully"
            }
            
        except Exception as e:
            error_str = str(e)
            
            # Handle token refresh needed
            if "QBO_UNAUTHORIZED" in error_str:
                # Try one refresh and retry
                try:
                    access_token, realm_id = await self.get_fresh_token(tenant_id)
                    result = await self.client.post_journal_entry(realm_id, access_token, qbo_payload)
                    
                    # Store idempotency and audit (same logic as above)
                    qbo_doc_id = result["qbo_doc_id"]
                    idempotency = JEIdempotencyDB(
                        tenant_id=tenant_id,
                        payload_hash=payload_hash,
                        qbo_doc_id=qbo_doc_id
                    )
                    self.db.add(idempotency)
                    
                    audit = DecisionAuditLogDB(
                        timestamp=datetime.utcnow(),
                        tenant_id=tenant_id,
                        action="QBO_JE_POSTED"
                    )
                    self.db.add(audit)
                    self.db.commit()
                    
                    return {
                        "status": 201,
                        "qbo_doc_id": qbo_doc_id,
                        "idempotent": False,
                        "message": "Journal entry posted successfully (after token refresh)"
                    }
                except Exception as refresh_error:
                    logger.error(f"QBO post failed after refresh: {refresh_error}")
                    raise
            
            # Re-raise for router to handle
            raise
    
    def get_connection_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get QBO connection status for tenant.
        
        Returns:
            {
                "connected": bool,
                "realm_id": str,
                "token_age_sec": int,
                "expires_in_sec": int
            }
        """
        token_record = self.db.query(QBOTokenDB).filter(
            QBOTokenDB.tenant_id == tenant_id
        ).first()
        
        if not token_record:
            return {
                "connected": False,
                "realm_id": None,
                "token_age_sec": None,
                "expires_in_sec": None
            }
        
        # Calculate token age
        token_age = (datetime.utcnow() - token_record.created_at).total_seconds()
        expires_in = (token_record.expires_at - datetime.utcnow()).total_seconds()
        
        return {
            "connected": True,
            "realm_id": token_record.realm_id,
            "token_age_sec": int(token_age),
            "expires_in_sec": int(max(0, expires_in))
        }

