"""
Decision output formatters with ordered trace and rationale.

Provides structured output for /api/transactions/propose with:
- Ordered execution trace (rule → embedding → llm)
- Confidence scores per method
- Rationale and explanation
- Audit trail
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def format_proposed_entry(
    transaction_id: str,
    description: str,
    amount: float,
    proposed_account: str,
    confidence: float,
    rule_score: Optional[Dict[str, Any]] = None,
    embedding_score: Optional[Dict[str, Any]] = None,
    llm_score: Optional[Dict[str, Any]] = None,
    method: str = "blended",
    route: str = "needs_review"
) -> Dict[str, Any]:
    """
    Format a single proposed journal entry with ordered trace.
    
    Args:
        transaction_id: Transaction identifier
        description: Transaction description
        amount: Transaction amount
        proposed_account: Proposed GL account
        confidence: Final blended confidence (0.0-1.0)
        rule_score: Rules engine result {score, account, matched_rule}
        embedding_score: Vector embedding result {score, account, cosine_similarity}
        llm_score: LLM categorization result {score, account, explanation}
        method: Decision method used (rule, embedding, llm, blended)
        route: Routing decision (auto_post, needs_review, human_review)
        
    Returns:
        Formatted dict with ordered trace and rationale
        
    Example:
        >>> format_proposed_entry(
        ...     transaction_id="tx_123",
        ...     description="Starbucks Coffee",
        ...     amount=4.50,
        ...     proposed_account="Meals & Entertainment",
        ...     confidence=0.93,
        ...     rule_score={"score": 0.95, "account": "Meals & Entertainment", 
        ...                 "matched_rule": "merchant_match_starbucks"},
        ...     embedding_score={"score": 0.88, "account": "Meals & Entertainment",
        ...                     "cosine_similarity": 0.88},
        ...     llm_score={"score": 0.90, "account": "Meals & Entertainment",
        ...               "explanation": "Coffee purchase at restaurant"},
        ...     method="blended"
        ... )
        {
            "tx_id": "tx_123",
            "description": "Starbucks Coffee",
            "amount": 4.50,
            "proposed_account": "Meals & Entertainment",
            "confidence": 0.93,
            "route": "auto_post",
            "method": "blended",
            "rationale": {
                "rule": {
                    "executed": True,
                    "confidence": 0.95,
                    "account": "Meals & Entertainment",
                    "details": "Matched rule: merchant_match_starbucks"
                },
                "embedding": {
                    "executed": True,
                    "confidence": 0.88,
                    "account": "Meals & Entertainment",
                    "details": "Cosine similarity: 0.88"
                },
                "llm": {
                    "executed": True,
                    "confidence": 0.90,
                    "account": "Meals & Entertainment",
                    "details": "Coffee purchase at restaurant"
                }
            },
            "execution_order": ["rule", "embedding", "llm"],
            "audit": {
                "timestamp": "2025-10-31T17:45:00Z",
                "model_version": "m1.0.0",
                "rule_version": "v0.0.1"
            }
        }
    """
    
    # Build ordered rationale
    rationale = {}
    execution_order = []
    
    # 1. Rules engine (always executed first)
    if rule_score:
        rationale["rule"] = {
            "executed": True,
            "confidence": rule_score.get("score", 0.0),
            "account": rule_score.get("account", "Unknown"),
            "details": _format_rule_details(rule_score)
        }
        execution_order.append("rule")
    else:
        rationale["rule"] = {
            "executed": False,
            "confidence": 0.0,
            "account": None,
            "details": "Rules engine not available"
        }
    
    # 2. Embedding / Vector similarity (executed second if available)
    if embedding_score:
        rationale["embedding"] = {
            "executed": True,
            "confidence": embedding_score.get("score", 0.0),
            "account": embedding_score.get("account", "Unknown"),
            "details": _format_embedding_details(embedding_score)
        }
        execution_order.append("embedding")
    else:
        rationale["embedding"] = {
            "executed": False,
            "confidence": 0.0,
            "account": None,
            "details": "Embedding vector store not available"
        }
    
    # 3. LLM (executed last, only if needed)
    if llm_score:
        rationale["llm"] = {
            "executed": True,
            "confidence": llm_score.get("score", 0.0),
            "account": llm_score.get("account", "Unknown"),
            "details": _format_llm_details(llm_score)
        }
        execution_order.append("llm")
    else:
        rationale["llm"] = {
            "executed": False,
            "confidence": 0.0,
            "account": None,
            "details": "LLM not invoked (high confidence from earlier methods)"
        }
    
    # Build response
    return {
        "tx_id": transaction_id,
        "description": description,
        "amount": amount,
        "proposed_account": proposed_account,
        "confidence": round(confidence, 3),
        "route": route,
        "method": method,
        "rationale": rationale,
        "execution_order": execution_order,
        "audit": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_version": "m1.0.0",  # From env or config
            "rule_version": "v0.0.1"    # From rule engine
        }
    }


def _format_rule_details(rule_score: Dict[str, Any]) -> str:
    """Format rules engine details for human readability."""
    matched_rule = rule_score.get("matched_rule")
    if matched_rule:
        return f"Matched rule: {matched_rule}"
    
    vendor = rule_score.get("vendor")
    if vendor:
        return f"Vendor match: {vendor}"
    
    keywords = rule_score.get("keywords", [])
    if keywords:
        return f"Keywords: {', '.join(keywords)}"
    
    return "Rule-based match"


def _format_embedding_details(embedding_score: Dict[str, Any]) -> str:
    """Format embedding/vector similarity details."""
    cosine_sim = embedding_score.get("cosine_similarity")
    if cosine_sim is not None:
        return f"Cosine similarity: {round(cosine_sim, 3)} (top-1 match)"
    
    nearest_neighbors = embedding_score.get("nearest_neighbors", 0)
    if nearest_neighbors:
        return f"Vector match from {nearest_neighbors} historical transactions"
    
    return "Embedding-based match"


def _format_llm_details(llm_score: Dict[str, Any]) -> str:
    """Format LLM explanation."""
    explanation = llm_score.get("explanation")
    if explanation:
        # Truncate to 200 chars for API response
        return explanation[:200] + ("..." if len(explanation) > 200 else "")
    
    reasoning = llm_score.get("reasoning")
    if reasoning:
        return reasoning[:200] + ("..." if len(reasoning) > 200 else "")
    
    return "LLM-based categorization"


def format_propose_response(
    proposed_entries: List[Dict[str, Any]],
    threshold: float,
    stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format full /api/transactions/propose response.
    
    Args:
        proposed_entries: List of formatted entries from format_proposed_entry()
        threshold: Confidence threshold used
        stats: Optional statistics {high_confidence_count, needs_review_count, ...}
        
    Returns:
        Complete API response dict
        
    Example:
        >>> format_propose_response(
        ...     proposed_entries=[...],
        ...     threshold=0.90,
        ...     stats={"high_confidence": 45, "needs_review": 3}
        ... )
        {
            "success": True,
            "entries": [...],
            "threshold": 0.90,
            "stats": {
                "total": 48,
                "high_confidence": 45,
                "needs_review": 3,
                "avg_confidence": 0.92
            },
            "metadata": {
                "timestamp": "2025-10-31T17:45:00Z",
                "model_version": "m1.0.0",
                "rule_version": "v0.0.1"
            }
        }
    """
    
    # Compute stats if not provided
    if stats is None:
        high_conf_count = sum(1 for e in proposed_entries if e["confidence"] >= threshold)
        needs_review_count = len(proposed_entries) - high_conf_count
        avg_conf = (
            sum(e["confidence"] for e in proposed_entries) / len(proposed_entries)
            if proposed_entries else 0.0
        )
        
        stats = {
            "total": len(proposed_entries),
            "high_confidence": high_conf_count,
            "needs_review": needs_review_count,
            "avg_confidence": round(avg_conf, 3)
        }
    
    return {
        "success": True,
        "entries": proposed_entries,
        "threshold": threshold,
        "stats": stats,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_version": "m1.0.0",
            "rule_version": "v0.0.1"
        }
    }


def format_audit_entry(
    transaction_id: str,
    tenant_id: str,
    proposed_entry: Dict[str, Any],
    user_action: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format audit log entry for decision_audit_log table.
    
    Args:
        transaction_id: Transaction identifier
        tenant_id: Tenant identifier
        proposed_entry: Output from format_proposed_entry()
        user_action: Optional user action (approved, rejected, modified)
        user_id: User who took action
        
    Returns:
        Dict ready for insertion into decision_audit_log
    """
    
    return {
        "transaction_id": transaction_id,
        "tenant_id": tenant_id,
        "proposed_account": proposed_entry["proposed_account"],
        "confidence": proposed_entry["confidence"],
        "method": proposed_entry["method"],
        "rationale": proposed_entry["rationale"],
        "execution_order": proposed_entry["execution_order"],
        "user_action": user_action,
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    }

