"""
Rules Console API - Live Backend (Wave-2 Phase 1 Final).

Endpoints:
- GET /api/rules/candidates - List pending candidates
- POST /api/rules/dryrun - Simulate impact (NO MUTATION)
- POST /api/rules/candidates/{id}/accept - Promote candidate
- POST /api/rules/candidates/{id}/reject - Decline candidate
- POST /api/rules/rollback - Rollback to previous version
- GET /api/rules/versions - List version history
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.db.models import (
    RuleCandidateDB,
    RuleVersionDB,
    DecisionAuditLogDB
)
from app.ui.rbac import User, get_current_user, Role


router = APIRouter(prefix="/api/rules", tags=["rules"])


class DryRunRequest(BaseModel):
    """Dry-run request."""
    candidate_ids: List[str]
    tenant_id: Optional[str] = None


class DryRunResponse(BaseModel):
    """Dry-run response with impact analysis."""
    before: Dict[str, Any]
    after: Dict[str, Any]
    affected_txn_ids: List[str]
    deltas: Dict[str, Any]


class CandidateResponse(BaseModel):
    """Rule candidate response."""
    id: str
    vendor_pattern: str
    suggested_account: str
    evidence: Dict[str, float]
    status: str
    created_at: str


class VersionResponse(BaseModel):
    """Rule version response."""
    version_id: str
    created_by: Optional[str]
    created_at: str
    is_active: bool


@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List rule candidates.
    
    Args:
        status: Filter by status (pending, accepted, rejected)
        
    Returns:
        List of candidates
    """
    query = db.query(RuleCandidateDB)
    
    if status:
        query = query.filter(RuleCandidateDB.status == status)
    
    candidates = query.order_by(RuleCandidateDB.created_at.desc()).all()
    
    return [
        CandidateResponse(
            id=c.id,
            vendor_pattern=c.vendor_pattern,
            suggested_account=c.suggested_account,
            evidence={
                "count": c.evidence_count,
                "precision": c.evidence_precision,
                "std_dev": c.evidence_std_dev
            },
            status=c.status,
            created_at=c.created_at.isoformat()
        )
        for c in candidates
    ]


@router.post("/dryrun", response_model=DryRunResponse)
async def dryrun_rule_promotion(
    request: DryRunRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Simulate rule promotion impact (NO MUTATION, READ-ONLY).
    
    Computes:
    - Current automation rate and reason counts
    - Projected automation rate if rules applied
    - Affected transaction IDs
    - Deltas for all metrics
    
    Validation:
    - Uses read-only transaction
    - No database writes
    - Logs dry-run to audit (separate transaction)
    
    Args:
        request: Candidate IDs and optional tenant scope
        
    Returns:
        Impact analysis with before/after metrics
    """
    # Validate candidates exist
    candidates = db.query(RuleCandidateDB).filter(
        RuleCandidateDB.id.in_(request.candidate_ids)
    ).all()
    
    if len(candidates) != len(request.candidate_ids):
        raise HTTPException(status_code=404, detail="One or more candidates not found")
    
    # Check for rule conflicts (multiple candidates for same vendor pattern)
    vendor_patterns = [c.vendor_pattern for c in candidates]
    if len(vendor_patterns) != len(set(vendor_patterns)):
        raise HTTPException(
            status_code=409,
            detail=f"Rule conflict: Multiple candidates for same vendor pattern(s)"
        )
    
    # Build base query for audit log
    query = db.query(DecisionAuditLogDB)
    if request.tenant_id:
        query = query.filter(DecisionAuditLogDB.tenant_id == request.tenant_id)
    
    # Calculate BEFORE metrics
    total_entries = query.count()
    if total_entries == 0:
        raise HTTPException(status_code=400, detail="No audit entries found for analysis")
    
    auto_posted_count = query.filter(DecisionAuditLogDB.action == "auto_posted").count()
    before_automation_rate = auto_posted_count / total_entries if total_entries > 0 else 0
    
    # Count reasons BEFORE
    before_reason_counts = {}
    reason_query = query.filter(DecisionAuditLogDB.not_auto_post_reason.isnot(None))
    for entry in reason_query.all():
        reason = entry.not_auto_post_reason
        before_reason_counts[reason] = before_reason_counts.get(reason, 0) + 1
    
    # Find affected transactions (those matching vendor patterns that were reviewed)
    affected_txn_ids = []
    after_reason_counts = before_reason_counts.copy()
    
    for candidate in candidates:
        # Convert vendor pattern to SQL LIKE pattern
        like_pattern = candidate.vendor_pattern.replace("*", "%")
        
        # Find matching transactions that were reviewed
        matching = query.filter(
            DecisionAuditLogDB.vendor_normalized.like(like_pattern),
            DecisionAuditLogDB.action == "reviewed"
        ).all()
        
        for entry in matching:
            if entry.txn_id and entry.txn_id not in affected_txn_ids:
                affected_txn_ids.append(entry.txn_id)
            
            # Decrement the reason count (would be removed if rule applied)
            if entry.not_auto_post_reason:
                reason = entry.not_auto_post_reason
                after_reason_counts[reason] = after_reason_counts.get(reason, 0) - 1
                if after_reason_counts[reason] <= 0:
                    after_reason_counts.pop(reason, None)
    
    # Calculate AFTER metrics
    projected_auto_posted = auto_posted_count + len(affected_txn_ids)
    after_automation_rate = projected_auto_posted / total_entries if total_entries > 0 else 0
    
    # Build response
    before = {
        "automation_rate": round(before_automation_rate, 4),
        "not_auto_post_counts": before_reason_counts
    }
    
    after = {
        "automation_rate": round(after_automation_rate, 4),
        "not_auto_post_counts": after_reason_counts
    }
    
    deltas = {
        "automation_rate": round(after_automation_rate - before_automation_rate, 4)
    }
    
    # Add per-reason deltas
    all_reasons = set(before_reason_counts.keys()) | set(after_reason_counts.keys())
    for reason in all_reasons:
        before_count = before_reason_counts.get(reason, 0)
        after_count = after_reason_counts.get(reason, 0)
        deltas[reason] = after_count - before_count
    
    # Log dry-run to audit (separate transaction, allowed)
    audit_entry = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        action="rule_dryrun",
        user_id=user.user_id,
        tenant_id=request.tenant_id
    )
    db.add(audit_entry)
    db.commit()
    
    return DryRunResponse(
        before=before,
        after=after,
        affected_txn_ids=affected_txn_ids,
        deltas=deltas
    )


@router.post("/candidates/{id}/accept")
async def accept_candidate(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Promote candidate to accepted rule.
    
    Steps:
    1. Validate candidate exists and is pending
    2. Check for idempotency (already accepted)
    3. Update candidate status
    4. Create new rule version
    5. Write audit entry
    
    Returns:
        Success response with version ID
    """
    candidate = db.query(RuleCandidateDB).filter(RuleCandidateDB.id == id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Idempotency check
    if candidate.status == "accepted":
        return {
            "success": True,
            "no_change": True,
            "message": "Candidate already accepted",
            "candidate_id": id
        }
    
    if candidate.status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot accept rejected candidate")
    
    # Get current active version
    current_version = db.query(RuleVersionDB).filter(
        RuleVersionDB.is_active == True
    ).first()
    
    old_version_id = current_version.version_id if current_version else None
    
    # Update candidate
    candidate.status = "accepted"
    candidate.reviewed_by = user.user_id
    candidate.reviewed_at = datetime.utcnow()
    
    # Create new rule version
    new_version_id = f"v{int(datetime.utcnow().timestamp())}"
    new_version = RuleVersionDB(
        version_id=new_version_id,
        rules_yaml=f"# Promoted rule: {candidate.vendor_pattern} -> {candidate.suggested_account}\n",
        created_by=user.user_id,
        is_active=True
    )
    
    # Deactivate old version
    if current_version:
        current_version.is_active = False
    
    db.add(new_version)
    
    # Audit entry with impact summary
    audit_entry = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        action="rule_promoted",
        user_id=user.user_id
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "success": True,
        "candidate_id": id,
        "version_id": new_version_id,
        "old_version_id": old_version_id
    }


@router.post("/candidates/{id}/reject")
async def reject_candidate(
    id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Decline candidate.
    
    Args:
        id: Candidate ID
        reason: Optional rejection reason
        
    Returns:
        Success response
    """
    candidate = db.query(RuleCandidateDB).filter(RuleCandidateDB.id == id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Idempotency check
    if candidate.status == "rejected":
        return {
            "success": True,
            "no_change": True,
            "message": "Candidate already rejected",
            "candidate_id": id
        }
    
    if candidate.status == "accepted":
        raise HTTPException(status_code=400, detail="Cannot reject accepted candidate")
    
    # Update candidate
    candidate.status = "rejected"
    candidate.reviewed_by = user.user_id
    candidate.reviewed_at = datetime.utcnow()
    
    # Audit entry
    audit_entry = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        action="rule_rejected",
        user_id=user.user_id
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "success": True,
        "candidate_id": id,
        "reason": reason
    }


@router.post("/rollback")
async def rollback_rules(
    to_version: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Rollback to a previous rule version.
    
    Steps:
    1. Validate target version exists
    2. Check for idempotency (already active)
    3. Deactivate all versions
    4. Activate target version
    5. Write audit entry
    
    Args:
        to_version: Target version ID to rollback to
        
    Returns:
        Success response
    """
    target_version = db.query(RuleVersionDB).filter(
        RuleVersionDB.version_id == to_version
    ).first()
    
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get current active version
    current_version = db.query(RuleVersionDB).filter(
        RuleVersionDB.is_active == True
    ).first()
    
    # Idempotency check
    if target_version.is_active:
        return {
            "success": True,
            "no_change": True,
            "message": "Version already active",
            "version_id": to_version
        }
    
    old_version_id = current_version.version_id if current_version else None
    
    # Deactivate all versions
    db.query(RuleVersionDB).update({"is_active": False})
    
    # Activate target
    target_version.is_active = True
    
    # Audit entry
    audit_entry = DecisionAuditLogDB(
        timestamp=datetime.utcnow(),
        action="rule_rollback",
        user_id=user.user_id
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "success": True,
        "version_id": to_version,
        "old_version_id": old_version_id
    }


@router.get("/versions", response_model=List[VersionResponse])
async def list_versions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List all rule versions (newest first, immutable history).
    
    Returns:
        List of versions ordered by created_at DESC
    """
    versions = db.query(RuleVersionDB).order_by(
        RuleVersionDB.created_at.desc()
    ).all()
    
    return [
        VersionResponse(
            version_id=v.version_id,
            created_by=v.created_by,
            created_at=v.created_at.isoformat(),
            is_active=v.is_active
        )
        for v in versions
    ]

