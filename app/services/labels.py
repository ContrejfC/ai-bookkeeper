"""
Label training service with privacy-preserving redaction.

Implements Plan B: Consent-gated, redacted training data collection.
"""

import hashlib
import json
import secrets
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import ConsentLogDB, LabelSaltDB, LabelEventDB


class LabelsService:
    """Service for privacy-preserving training data collection."""
    
    def __init__(self, db: Session):
        self.db = db
        self.salt_rounds = int(os.getenv("LABEL_SALT_ROUNDS", "12"))
    
    def get_consent(self, tenant_id: str) -> bool:
        """
        Check if tenant has opted into training data collection.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            True if opted in, False otherwise (default: False)
        """
        latest = self.db.query(ConsentLogDB).filter(
            ConsentLogDB.tenant_id == tenant_id
        ).order_by(desc(ConsentLogDB.created_at)).first()
        
        if not latest:
            return False  # Default: opt-out
        
        return latest.state == 'opt_in'
    
    def set_consent(self, tenant_id: str, opt_in: bool, actor: Optional[str] = None) -> ConsentLogDB:
        """
        Set consent for training data collection.
        
        Args:
            tenant_id: Tenant identifier
            opt_in: True to opt in, False to opt out
            actor: User who changed consent (optional)
        
        Returns:
            Consent log entry
        """
        state = 'opt_in' if opt_in else 'opt_out'
        
        entry = ConsentLogDB(
            tenant_id=tenant_id,
            state=state,
            actor=actor
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    def get_salt(self, tenant_id: str) -> str:
        """
        Get current salt for tenant (create if doesn't exist).
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Hex-encoded salt
        """
        latest = self.db.query(LabelSaltDB).filter(
            LabelSaltDB.tenant_id == tenant_id
        ).order_by(desc(LabelSaltDB.rotated_at)).first()
        
        if latest:
            return latest.salt
        
        # Create new salt
        salt = secrets.token_hex(32)  # 256 bits
        salt_entry = LabelSaltDB(
            tenant_id=tenant_id,
            salt=salt
        )
        self.db.add(salt_entry)
        self.db.commit()
        
        return salt
    
    def rotate_salt(self, tenant_id: str) -> str:
        """
        Rotate salt for tenant (creates new salt).
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            New hex-encoded salt
        """
        new_salt = secrets.token_hex(32)
        salt_entry = LabelSaltDB(
            tenant_id=tenant_id,
            salt=new_salt
        )
        self.db.add(salt_entry)
        self.db.commit()
        
        return new_salt
    
    def redact_value(self, value: str, tenant_id: str) -> str:
        """
        Redact sensitive value using tenant salt.
        
        Args:
            value: Value to redact
            tenant_id: Tenant identifier
        
        Returns:
            SHA-256 hash (hex) of value + salt
        """
        salt = self.get_salt(tenant_id)
        combined = f"{value}:{salt}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def redact_payload(self, payload: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Redact sensitive fields in training payload.
        
        Redacts:
        - vendor strings → hashed
        - description → hashed
        - amounts → rounded to cents
        - account names → preserved (not PII)
        - confidence → preserved
        
        Args:
            payload: Original training payload
            tenant_id: Tenant identifier
        
        Returns:
            Redacted payload
        """
        redacted = payload.copy()
        
        # Redact vendor/description
        if 'vendor' in redacted:
            redacted['vendor'] = self.redact_value(redacted['vendor'], tenant_id)
        if 'description' in redacted:
            redacted['description'] = self.redact_value(redacted['description'], tenant_id)
        
        # Round amounts
        if 'amount' in redacted:
            redacted['amount'] = round(float(redacted['amount']), 2)
        if 'debit' in redacted:
            redacted['debit'] = round(float(redacted['debit']), 2)
        if 'credit' in redacted:
            redacted['credit'] = round(float(redacted['credit']), 2)
        
        # Preserve: account, confidence, date (not PII)
        # Remove: raw transaction IDs, internal IDs
        redacted.pop('txn_id', None)
        redacted.pop('id', None)
        
        return redacted
    
    def store_label_event(
        self,
        tenant_id: str,
        payload: Dict[str, Any],
        approved: bool
    ) -> Optional[LabelEventDB]:
        """
        Store a redacted label event (if consent given).
        
        Args:
            tenant_id: Tenant identifier
            payload: Original payload to redact and store
            approved: Whether user approved the proposal
        
        Returns:
            LabelEventDB if stored, None if consent not given
        """
        # Check consent
        if not self.get_consent(tenant_id):
            return None  # Do not store if not opted in
        
        # Redact payload
        redacted = self.redact_payload(payload, tenant_id)
        
        # Store
        event = LabelEventDB(
            tenant_id=tenant_id,
            payload_redacted=json.dumps(redacted),
            approved_bool=approved
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def export_labels(
        self,
        tenant_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export redacted label events for tenant.
        
        Args:
            tenant_id: Tenant identifier
            since: Start date (optional)
            until: End date (optional)
        
        Returns:
            List of redacted payloads
        """
        query = self.db.query(LabelEventDB).filter(
            LabelEventDB.tenant_id == tenant_id
        )
        
        if since:
            query = query.filter(LabelEventDB.created_at >= since)
        if until:
            query = query.filter(LabelEventDB.created_at <= until)
        
        events = query.order_by(LabelEventDB.created_at).all()
        
        return [
            {
                "id": event.id,
                "payload": json.loads(event.payload_redacted),
                "approved": event.approved_bool,
                "created_at": event.created_at.isoformat()
            }
            for event in events
        ]
    
    def purge_labels(self, tenant_id: str) -> int:
        """
        Purge all label events for tenant and rotate salt.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Number of events deleted
        """
        # Count events
        count = self.db.query(LabelEventDB).filter(
            LabelEventDB.tenant_id == tenant_id
        ).count()
        
        # Delete events
        self.db.query(LabelEventDB).filter(
            LabelEventDB.tenant_id == tenant_id
        ).delete()
        
        # Rotate salt
        self.rotate_salt(tenant_id)
        
        self.db.commit()
        
        return count

