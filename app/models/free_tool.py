"""
Free Tool Database Models
=========================

Models for free categorizer uploads, consent tracking, and lead capture.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()


class FreeUploadDB(Base):
    """
    Tracks free tool uploads with retention and consent.
    
    These records are automatically purged after expires_at.
    """
    __tablename__ = "free_uploads"
    
    id = Column(String(36), primary_key=True)  # UUID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # created_at + retention_hours
    
    # File metadata
    filename = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    source_ext = Column(String(10), nullable=False)  # csv, pdf, etc
    row_count = Column(Integer, nullable=True)
    
    # Consent & compliance
    consent_training = Column(Boolean, default=False, nullable=False)
    consent_ts = Column(DateTime, nullable=True)
    ip_hash = Column(String(64), nullable=True)  # SHA256 of IP + salt
    session_id = Column(String(64), nullable=True)
    user_id = Column(String(36), nullable=True)  # If logged in
    file_hash = Column(String(64), nullable=True)  # SHA256 of file
    
    # Retention scope
    retention_scope = Column(String(20), default='ephemeral', nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<FreeUpload(id={self.id}, filename={self.filename}, expires={self.expires_at})>"


class FreeLeadDB(Base):
    """
    Tracks leads captured from free tool email gate.
    """
    __tablename__ = "free_leads"
    
    id = Column(String(36), primary_key=True)  # UUID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    email = Column(String(255), nullable=False)
    upload_id = Column(String(36), nullable=False)  # FK to free_uploads
    row_count = Column(Integer, nullable=True)
    
    # Source tracking
    source = Column(String(50), default='free_categorizer', nullable=False)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    
    # Privacy
    ip_hash = Column(String(64), nullable=True)
    
    # Status
    contacted = Column(Boolean, default=False, nullable=False)
    converted = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<FreeLead(id={self.id}, email={self.email}, source={self.source})>"


class ConsentLogDB(Base):
    """
    Audit log for training consent decisions.
    """
    __tablename__ = "consent_logs"
    
    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    upload_id = Column(String(36), nullable=False)
    consent_granted = Column(Boolean, nullable=False)
    
    # Privacy-preserving metadata
    file_hash_prefix = Column(String(16), nullable=True)  # First 16 chars of file hash
    session_id = Column(String(64), nullable=True)
    user_id = Column(String(36), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<ConsentLog(id={self.id}, consent={self.consent_granted})>"

