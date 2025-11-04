"""
Bank Statement Templates
========================

Template registry and matching system for bank statement recognition.
"""

from app.ingestion.templates.schema import (
    BankTemplate,
    MatchCriteria,
    ScoreWeights,
    TemplateMatchResult
)
from app.ingestion.templates.registry import TemplateRegistry

__all__ = [
    'BankTemplate',
    'MatchCriteria',
    'ScoreWeights',
    'TemplateMatchResult',
    'TemplateRegistry',
]



