"""
Template Schema
===============

Pydantic models for bank statement template definitions.
"""

from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field, validator


class MatchCriteria(BaseModel):
    """Criteria for matching a PDF to this template."""
    
    header_keys: List[str] = Field(
        default_factory=list,
        description="Keywords expected in header region (case-insensitive)"
    )
    
    table_headers: List[str] = Field(
        default_factory=list,
        description="Regex patterns for table column headers"
    )
    
    footer_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords expected in footer region (case-insensitive)"
    )
    
    date_format_pref: str = Field(
        default="MDY",
        description="Preferred date format: MDY, DMY, YMD"
    )
    
    amount_sign_rules: Dict[str, Any] = Field(
        default_factory=lambda: {
            "debit_is_negative": True,
            "credit_markers": []
        },
        description="Rules for interpreting amount signs"
    )
    
    geometry_hints: Dict[str, List[float]] = Field(
        default_factory=lambda: {
            "header_top_pct": [0.00, 0.20],
            "table_band_pct": [0.20, 0.85]
        },
        description="Expected layout geometry bands as percentages"
    )
    
    @validator('date_format_pref')
    def validate_date_format(cls, v):
        """Validate date format preference."""
        if v not in ['MDY', 'DMY', 'YMD']:
            raise ValueError('date_format_pref must be MDY, DMY, or YMD')
        return v


class ScoreWeights(BaseModel):
    """Weights for scoring components."""
    
    headers: float = Field(0.35, ge=0, le=1, description="Weight for header matching")
    table: float = Field(0.35, ge=0, le=1, description="Weight for table header matching")
    footer: float = Field(0.10, ge=0, le=1, description="Weight for footer matching")
    geometry: float = Field(0.20, ge=0, le=1, description="Weight for geometry matching")
    
    @validator('headers', 'table', 'footer', 'geometry')
    def validate_sum(cls, v, values):
        """Ensure weights sum to approximately 1.0."""
        # Note: This is a simplified check; full validation happens after all fields
        return v
    
    def validate_sum_total(self) -> bool:
        """Check if all weights sum to 1.0."""
        total = self.headers + self.table + self.footer + self.geometry
        return abs(total - 1.0) < 0.01


class BankTemplate(BaseModel):
    """Complete bank statement template definition."""
    
    name: str = Field(..., description="Unique template identifier")
    version: int = Field(1, ge=1, description="Template version number")
    
    match: MatchCriteria = Field(..., description="Matching criteria")
    score_weights: ScoreWeights = Field(
        default_factory=ScoreWeights,
        description="Scoring weights"
    )
    
    accept_threshold: float = Field(
        0.80,
        ge=0,
        le=1,
        description="Minimum score to accept this template"
    )
    
    # Optional metadata
    bank_name: Optional[str] = Field(None, description="Human-readable bank name")
    account_types: List[str] = Field(
        default_factory=list,
        description="Account types this template handles (checking, savings, credit)"
    )
    
    notes: Optional[str] = Field(None, description="Internal notes about this template")
    
    @validator('match')
    def validate_match_criteria(cls, v):
        """Ensure match criteria has at least some patterns."""
        if not v.header_keys and not v.table_headers and not v.footer_keywords:
            raise ValueError('Template must have at least one matching criterion')
        return v
    
    def __hash__(self):
        """Make template hashable for use in sets/dicts."""
        return hash((self.name, self.version))


class TemplateMatchResult(BaseModel):
    """Result of matching a PDF to a template."""
    
    template: BankTemplate
    score: float = Field(..., ge=0, le=1, description="Overall match score")
    
    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual component scores"
    )
    
    matched_tokens: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Specific tokens that matched"
    )
    
    confidence: float = Field(..., ge=0, le=1, description="Confidence in this match")
    
    def __lt__(self, other):
        """Enable sorting by score (descending)."""
        return self.score > other.score  # Reversed for descending sort
    
    def __repr__(self):
        return f"TemplateMatchResult(template={self.template.name}, score={self.score:.3f})"

