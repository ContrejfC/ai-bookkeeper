"""
Decision Blending Engine

Combines signals from Rules, ML, and LLM with weighted scoring:
- Configurable weights (W_RULES, W_ML, W_LLM)
- Transparent threshold-based routing
- Full audit trail
"""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.rules.schemas import (
    SignalScore, BlendedDecision, DecisionBlend
)

logger = logging.getLogger(__name__)


class DecisionBlender:
    """
    Blends multiple decision signals into a final decision.
    """
    
    def __init__(self, config: Optional[DecisionBlend] = None):
        """
        Initialize decision blender.
        
        Args:
            config: Blending configuration (uses defaults if None)
        """
        self.config = config or DecisionBlend()
        
        # Validate weights
        if not self.config.validate_weights():
            logger.warning(
                f"Weights don't sum to 1.0: "
                f"R={self.config.w_rules}, M={self.config.w_ml}, L={self.config.w_llm}"
            )
        
        logger.info(
            f"DecisionBlender initialized: "
            f"W_RULES={self.config.w_rules}, W_ML={self.config.w_ml}, W_LLM={self.config.w_llm}"
        )
    
    def blend(
        self,
        rule_score: SignalScore,
        ml_score: SignalScore,
        llm_score: Optional[SignalScore] = None,
        rule_version: Optional[str] = None
    ) -> BlendedDecision:
        """
        Blend signals from Rules, ML, and optionally LLM.
        
        Args:
            rule_score: Score from rules engine
            ml_score: Score from ML classifier
            llm_score: Optional score from LLM validator
            rule_version: Current rule version ID
            
        Returns:
            Blended decision with routing
        """
        # Compute weighted blend
        blend_value = (
            self.config.w_rules * rule_score.score +
            self.config.w_ml * ml_score.score
        )
        
        if llm_score:
            blend_value += self.config.w_llm * llm_score.score
        else:
            # Redistribute LLM weight if not available
            blend_value += self.config.w_llm * max(rule_score.score, ml_score.score)
        
        # Determine final account (highest individual score)
        candidates = [
            (rule_score.score, rule_score.account),
            (ml_score.score, ml_score.account)
        ]
        if llm_score and llm_score.account:
            candidates.append((llm_score.score, llm_score.account))
        
        # Sort by score descending
        candidates.sort(reverse=True, key=lambda x: x[0])
        final_account = candidates[0][1] if candidates else "Unknown"
        
        # Route based on blend score and thresholds
        route = self._determine_route(blend_value, rule_score, ml_score, llm_score)
        
        # Build signal breakdown
        signal_breakdown = {
            'rules': rule_score,
            'ml': ml_score
        }
        if llm_score:
            signal_breakdown['llm'] = llm_score
        
        # Create decision
        decision = BlendedDecision(
            final_account=final_account,
            blend_score=blend_value,
            signal_breakdown=signal_breakdown,
            route=route,
            thresholds={
                'AUTO_POST_MIN': self.config.auto_post_min,
                'REVIEW_MIN': self.config.review_min
            },
            rule_version=rule_version,
            timestamp=datetime.now()
        )
        
        logger.debug(
            f"Blended decision: {final_account} (score={blend_value:.3f}, route={route})"
        )
        
        return decision
    
    def _determine_route(
        self,
        blend_score: float,
        rule_score: SignalScore,
        ml_score: SignalScore,
        llm_score: Optional[SignalScore]
    ) -> str:
        """
        Determine routing based on blend score and thresholds.
        
        Args:
            blend_score: Weighted blend score
            rule_score, ml_score, llm_score: Individual scores
            
        Returns:
            Route: 'auto_post', 'needs_review', 'llm_validation', 'human_review'
        """
        # Auto-post if high confidence
        if blend_score >= self.config.auto_post_min:
            return "auto_post"
        
        # Needs review if moderate confidence
        if blend_score >= self.config.review_min:
            return "needs_review"
        
        # LLM validation if available and not already used
        if not llm_score and blend_score >= 0.70:
            return "llm_validation"
        
        # Human review for low confidence
        return "human_review"
    
    def update_config(self, new_config: DecisionBlend):
        """
        Update blending configuration.
        
        Args:
            new_config: New configuration
        """
        if not new_config.validate_weights():
            raise ValueError("Weights must sum to 1.0")
        
        self.config = new_config
        logger.info(f"Updated config: {new_config}")


def create_decision_blender(config: Optional[DecisionBlend] = None) -> DecisionBlender:
    """Factory to create decision blender."""
    return DecisionBlender(config)

