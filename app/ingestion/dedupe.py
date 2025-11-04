"""
Transaction Deduplication
=========================

Detect and mark duplicate transactions across uploads using fingerprinting.
"""

import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.ingestion.config import config
from app.ingestion.schemas import CanonicalTransaction

logger = logging.getLogger(__name__)


def generate_fingerprint(
    account_id: str,
    post_date: datetime,
    amount: Decimal,
    description: str
) -> str:
    """
    Generate a fingerprint for deduplication.
    
    Fingerprint = SHA-1(account_id|post_date|round(amount,2)|norm(description))
    
    Args:
        account_id: Account identifier
        post_date: Transaction posting date
        amount: Transaction amount
        description: Transaction description
    
    Returns:
        64-character SHA-1 hex digest
    """
    # Round amount to configured decimals
    rounded_amount = round(float(amount), config.DEDUP_FINGERPRINT_ROUND_DECIMALS)
    
    # Normalize description (lowercase, remove extra spaces)
    norm_desc = ' '.join(description.lower().split())
    
    # Format date as YYYY-MM-DD
    date_str = post_date.strftime('%Y-%m-%d') if isinstance(post_date, datetime) else str(post_date)
    
    # Create fingerprint string
    fingerprint_str = f"{account_id}|{date_str}|{rounded_amount:.2f}|{norm_desc}"
    
    # Generate SHA-1 hash
    return hashlib.sha1(fingerprint_str.encode('utf-8')).hexdigest()


def check_duplicate(
    db: Session,
    tenant_id: UUID,
    fingerprint: str
) -> Optional[UUID]:
    """
    Check if a transaction with this fingerprint already exists.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        fingerprint: Transaction fingerprint
    
    Returns:
        UUID of existing transaction if found, None otherwise
    """
    try:
        from app.ingestion.models import Transaction
        
        existing = (
            db.query(Transaction.id)
            .filter(
                and_(
                    Transaction.tenant_id == tenant_id,
                    Transaction.fingerprint == fingerprint
                )
            )
            .first()
        )
        
        if existing:
            logger.debug(f"Found duplicate with fingerprint {fingerprint[:16]}...")
            return existing[0]
        
        return None
    
    except Exception as e:
        logger.error(f"Error checking duplicate: {e}")
        return None


def deduplicate_batch(
    db: Session,
    tenant_id: UUID,
    transactions: List[CanonicalTransaction]
) -> Tuple[List[CanonicalTransaction], List[CanonicalTransaction], int]:
    """
    Deduplicate a batch of transactions.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        transactions: List of canonical transactions
    
    Returns:
        Tuple of (unique_transactions, duplicate_transactions, existing_duplicates_count)
    """
    unique = []
    duplicates = []
    existing_count = 0
    seen_fingerprints = set()
    
    for txn in transactions:
        # Generate fingerprint
        fingerprint = generate_fingerprint(
            account_id=txn.account_id,
            post_date=txn.post_date,
            amount=txn.amount,
            description=txn.description
        )
        
        # Check if duplicate within this batch
        if fingerprint in seen_fingerprints:
            duplicates.append(txn)
            logger.debug(f"Batch duplicate detected: {txn.description[:50]}")
            continue
        
        # Check if duplicate in database
        existing_id = check_duplicate(db, tenant_id, fingerprint)
        if existing_id:
            # Mark as duplicate of existing
            txn_dict = txn.dict()
            txn_dict['duplicate_of'] = existing_id
            duplicates.append(CanonicalTransaction(**txn_dict))
            existing_count += 1
            logger.debug(f"Database duplicate detected: {txn.description[:50]}")
            continue
        
        # Unique transaction
        seen_fingerprints.add(fingerprint)
        unique.append(txn)
    
    logger.info(
        f"Deduplication: {len(unique)} unique, "
        f"{len(duplicates)} duplicates "
        f"({existing_count} against existing records)"
    )
    
    return unique, duplicates, existing_count


def get_duplicate_transactions(
    db: Session,
    tenant_id: UUID,
    file_id: Optional[UUID] = None,
    limit: int = 100
) -> List[dict]:
    """
    Get transactions that are marked as duplicates.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        file_id: Optional file ID to filter by
        limit: Maximum number of results
    
    Returns:
        List of duplicate transaction records with metadata
    """
    try:
        from app.ingestion.models import Transaction
        
        query = (
            db.query(Transaction)
            .filter(
                and_(
                    Transaction.tenant_id == tenant_id,
                    Transaction.duplicate_of.isnot(None)
                )
            )
        )
        
        if file_id:
            query = query.filter(Transaction.file_id == file_id)
        
        duplicates = query.limit(limit).all()
        
        return [
            {
                'id': str(txn.id),
                'description': txn.description,
                'amount': txn.amount,
                'post_date': txn.post_date.isoformat(),
                'fingerprint': txn.fingerprint,
                'duplicate_of': str(txn.duplicate_of),
                'file_id': str(txn.file_id)
            }
            for txn in duplicates
        ]
    
    except Exception as e:
        logger.error(f"Error getting duplicates: {e}")
        return []


def get_deduplication_stats(
    db: Session,
    tenant_id: UUID,
    file_id: Optional[UUID] = None
) -> dict:
    """
    Get deduplication statistics.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        file_id: Optional file ID to filter by
    
    Returns:
        Dictionary with deduplication stats
    """
    try:
        from app.ingestion.models import Transaction
        from sqlalchemy import func
        
        # Base query
        base_query = db.query(Transaction).filter(Transaction.tenant_id == tenant_id)
        
        if file_id:
            base_query = base_query.filter(Transaction.file_id == file_id)
        
        # Count totals
        total = base_query.count()
        duplicates = base_query.filter(Transaction.duplicate_of.isnot(None)).count()
        unique = total - duplicates
        
        # Get duplicate rate
        duplicate_rate = (duplicates / total * 100) if total > 0 else 0
        
        return {
            'total_transactions': total,
            'unique_transactions': unique,
            'duplicate_transactions': duplicates,
            'duplicate_rate_percent': round(duplicate_rate, 2)
        }
    
    except Exception as e:
        logger.error(f"Error getting dedup stats: {e}")
        return {
            'total_transactions': 0,
            'unique_transactions': 0,
            'duplicate_transactions': 0,
            'duplicate_rate_percent': 0.0
        }


def recompute_fingerprints(
    db: Session,
    tenant_id: UUID,
    file_id: Optional[UUID] = None
) -> int:
    """
    Recompute fingerprints for existing transactions.
    
    Useful after changing fingerprint algorithm or fixing data issues.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        file_id: Optional file ID to limit scope
    
    Returns:
        Number of transactions updated
    """
    try:
        from app.ingestion.models import Transaction
        
        query = db.query(Transaction).filter(Transaction.tenant_id == tenant_id)
        
        if file_id:
            query = query.filter(Transaction.file_id == file_id)
        
        transactions = query.all()
        updated = 0
        
        for txn in transactions:
            old_fingerprint = txn.fingerprint
            new_fingerprint = generate_fingerprint(
                account_id=txn.account_id,
                post_date=txn.post_date,
                amount=txn.amount,
                description=txn.description
            )
            
            if old_fingerprint != new_fingerprint:
                txn.fingerprint = new_fingerprint
                updated += 1
        
        db.commit()
        
        logger.info(f"Recomputed {updated} fingerprints for tenant {tenant_id}")
        return updated
    
    except Exception as e:
        logger.error(f"Error recomputing fingerprints: {e}")
        db.rollback()
        return 0



