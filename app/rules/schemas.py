"""
Rule and candidate schemas for adaptive rule learning.

Defines data structures for:
- Rule definitions (exact, regex, MCC-scoped)
- Candidate rules (pending promotion)
- Rule versions (immutable history)
- Evidence aggregation
"""
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class RuleMatch(BaseModel):
    """Result of a rule match."""
    matched: bool
    account: Optional[str] = None
    confidence: float = 0.0
    match_type: Literal["exact", "regex", "mcc", "memo", "none"] = "none"
    rule_id: Optional[str] = None
    pattern: Optional[str] = None
    source_file: Optional[str] = None


class RuleEvidence(BaseModel):
    """Evidence for a candidate rule."""
    vendor_normalized: str
    suggested_account: str
    confidence: float
    source: Literal["user_override", "ml_prediction", "llm_validation"]
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleCandidate(BaseModel):
    """Candidate rule awaiting review."""
    id: Optional[int] = None
    vendor_normalized: str
    pattern: Optional[str] = None
    suggested_account: str
    obs_count: int = 0
    avg_confidence: float = 0.0
    variance: float = 0.0
    last_seen_at: Optional[datetime] = None
    reasons_json: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "accepted", "rejected"] = "pending"
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RuleVersion(BaseModel):
    """Immutable rule version."""
    id: Optional[int] = None
    version: str
    created_at: datetime = Field(default_factory=datetime.now)
    author: str = "system"
    path: str
    notes: Optional[str] = None
    rule_count: int = 0
    
    class Config:
        from_attributes = True


class RuleDefinition(BaseModel):
    """A single rule definition."""
    id: str
    type: Literal["exact_vendor", "regex_pattern", "mcc_default", "memo_contains"]
    pattern: str
    account: str
    confidence: float = 1.0
    priority: int = 100
    enabled: bool = True
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PromotionPolicy(BaseModel):
    """Policy for promoting candidates to rules."""
    min_observations: int = 3
    min_confidence: float = 0.85
    max_variance: float = 0.08
    conf_delta_min: float = 0.15


class DecisionBlend(BaseModel):
    """Decision blending configuration."""
    w_rules: float = 0.55
    w_ml: float = 0.35
    w_llm: float = 0.10
    auto_post_min: float = 0.90
    review_min: float = 0.75
    
    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0."""
        return abs((self.w_rules + self.w_ml + self.w_llm) - 1.0) < 0.01


class SignalScore(BaseModel):
    """Score from a single decision signal (Rules, ML, or LLM)."""
    source: Literal["rules", "ml", "llm"]
    score: float = 0.0
    account: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlendedDecision(BaseModel):
    """Final blended decision from all signals."""
    final_account: str
    blend_score: float
    signal_breakdown: Dict[str, SignalScore]
    route: Literal["auto_post", "needs_review", "llm_validation", "human_review"]
    thresholds: Dict[str, float]
    rule_version: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class Explanation(BaseModel):
    """Explanation for a decision."""
    transaction_id: str
    final_account: str
    blend_score: float
    signal_breakdown: Dict[str, Any]
    thresholds: Dict[str, float]
    rule_version: Optional[str] = None
    audit: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123",
                "final_account": "Office Supplies",
                "blend_score": 0.93,
                "signal_breakdown": {
                    "rules": {
                        "score": 0.98,
                        "match_type": "regex",
                        "rule_id": "rv-023"
                    },
                    "ml": {
                        "score": 0.89,
                        "top_features": [
                            {"term": "staples", "weight": 0.31},
                            {"term": "office", "weight": 0.24}
                        ]
                    },
                    "llm": {
                        "score": 0.66,
                        "rationale": "Receipt shows office items"
                    }
                },
                "thresholds": {
                    "AUTO_POST_MIN": 0.90,
                    "REVIEW_MIN": 0.75
                },
                "rule_version": "v0.4.12"
            }
        }


class DryRunImpact(BaseModel):
    """Impact analysis from dry-run simulation."""
    automation_pct_before: float
    automation_pct_after: float
    automation_pct_delta: float
    conflicts: int
    affected_transactions: int
    safety_flags: List[str] = Field(default_factory=list)
    sample_changes: List[Dict[str, Any]] = Field(default_factory=list)

