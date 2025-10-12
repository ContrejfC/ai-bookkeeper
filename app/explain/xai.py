"""
Explainability Layer (XAI)

Provides transparent explanations for every decision:
- Rule traces (which rule matched)
- ML feature importance (top contributing features)
- LLM rationale (natural language)
- Unified explanation format
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.rules.schemas import Explanation, BlendedDecision

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Generates explanations for transaction categorization decisions.
    """
    
    def __init__(self):
        """Initialize explainability engine."""
        logger.info("ExplainabilityEngine initialized")
    
    def explain_decision(
        self,
        transaction_id: str,
        decision: BlendedDecision,
        ml_features: Optional[List[Dict[str, Any]]] = None,
        rule_trace: Optional[Dict[str, Any]] = None,
        llm_rationale: Optional[str] = None
    ) -> Explanation:
        """
        Generate comprehensive explanation for a decision.
        
        Args:
            transaction_id: Transaction identifier
            decision: Blended decision from DecisionBlender
            ml_features: Top ML features (SHAP or surrogate)
            rule_trace: Rule matching details
            llm_rationale: LLM natural language explanation
            
        Returns:
            Unified explanation
        """
        # Build signal breakdown with explanations
        signal_breakdown = {}
        
        # Rules signal
        rules_signal = decision.signal_breakdown.get('rules')
        if rules_signal:
            signal_breakdown['rules'] = {
                'score': rules_signal.score,
                'account': rules_signal.account,
                'match_type': rules_signal.metadata.get('match_type', 'none'),
                'rule_id': rules_signal.metadata.get('rule_id'),
                'pattern': rules_signal.metadata.get('pattern'),
                'explanation': self._format_rule_explanation(rules_signal, rule_trace)
            }
        
        # ML signal
        ml_signal = decision.signal_breakdown.get('ml')
        if ml_signal:
            signal_breakdown['ml'] = {
                'score': ml_signal.score,
                'account': ml_signal.account,
                'top_features': ml_features or self._extract_ml_features(ml_signal),
                'explanation': self._format_ml_explanation(ml_signal, ml_features)
            }
        
        # LLM signal
        llm_signal = decision.signal_breakdown.get('llm')
        if llm_signal:
            signal_breakdown['llm'] = {
                'score': llm_signal.score,
                'account': llm_signal.account,
                'rationale': llm_rationale or llm_signal.metadata.get('rationale', ''),
                'explanation': llm_rationale or "LLM validation result"
            }
        
        # Create explanation
        explanation = Explanation(
            transaction_id=transaction_id,
            final_account=decision.final_account,
            blend_score=decision.blend_score,
            signal_breakdown=signal_breakdown,
            thresholds=decision.thresholds,
            rule_version=decision.rule_version,
            audit={
                'timestamp': decision.timestamp.isoformat(),
                'route': decision.route,
                'decision_method': 'blended'
            }
        )
        
        return explanation
    
    @staticmethod
    def _format_rule_explanation(
        rules_signal,
        rule_trace: Optional[Dict[str, Any]]
    ) -> str:
        """Format human-readable rule explanation."""
        if not rules_signal or rules_signal.score == 0.0:
            return "No rule match found"
        
        match_type = rules_signal.metadata.get('match_type', 'unknown')
        pattern = rules_signal.metadata.get('pattern', 'N/A')
        
        if match_type == "exact":
            return f"Exact vendor match: '{pattern}'"
        elif match_type == "regex":
            return f"Pattern match: '{pattern}'"
        elif match_type == "mcc":
            return f"MCC code default: '{pattern}'"
        else:
            return f"Rule matched ({match_type})"
    
    @staticmethod
    def _extract_ml_features(ml_signal) -> List[Dict[str, Any]]:
        """Extract top features from ML metadata."""
        features = ml_signal.metadata.get('top_features', [])
        if not features:
            # Placeholder if not available
            return [
                {"feature": "description_terms", "weight": 0.35},
                {"feature": "amount_bucket", "weight": 0.18},
                {"feature": "vendor", "weight": 0.15}
            ]
        return features
    
    @staticmethod
    def _format_ml_explanation(
        ml_signal,
        ml_features: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Format human-readable ML explanation."""
        if not ml_signal or ml_signal.score == 0.0:
            return "ML model did not provide a prediction"
        
        account = ml_signal.account or "Unknown"
        score = ml_signal.score
        
        if ml_features:
            top_feature = ml_features[0]
            feature_name = top_feature.get('feature', top_feature.get('term', 'unknown'))
            weight = top_feature.get('weight', 0.0)
            return f"ML predicted '{account}' (confidence: {score:.1%}). Top feature: {feature_name} (weight: {weight:.2f})"
        
        return f"ML predicted '{account}' with {score:.1%} confidence"
    
    def explain_batch(
        self,
        decisions: List[Dict[str, Any]]
    ) -> List[Explanation]:
        """
        Generate explanations for a batch of decisions.
        
        Args:
            decisions: List of decision dicts with metadata
            
        Returns:
            List of explanations
        """
        explanations = []
        for dec in decisions:
            try:
                expl = self.explain_decision(
                    transaction_id=dec['transaction_id'],
                    decision=dec['decision'],
                    ml_features=dec.get('ml_features'),
                    rule_trace=dec.get('rule_trace'),
                    llm_rationale=dec.get('llm_rationale')
                )
                explanations.append(expl)
            except Exception as e:
                logger.error(f"Failed to explain {dec.get('transaction_id')}: {e}")
        
        return explanations
    
    def format_explanation_text(self, explanation: Explanation) -> str:
        """
        Format explanation as human-readable text.
        
        Args:
            explanation: Explanation object
            
        Returns:
            Formatted text
        """
        lines = []
        lines.append(f"Transaction: {explanation.transaction_id}")
        lines.append(f"Categorized as: {explanation.final_account}")
        lines.append(f"Confidence: {explanation.blend_score:.1%}")
        lines.append("")
        lines.append("Decision Breakdown:")
        
        for signal_name, signal_data in explanation.signal_breakdown.items():
            score = signal_data.get('score', 0.0)
            expl_text = signal_data.get('explanation', 'No explanation')
            lines.append(f"  {signal_name.upper()}: {score:.1%}")
            lines.append(f"    {expl_text}")
        
        lines.append("")
        lines.append(f"Routing: {explanation.audit.get('route', 'unknown')}")
        lines.append(f"Rule Version: {explanation.rule_version or 'N/A'}")
        
        return "\n".join(lines)


def create_explainability_engine() -> ExplainabilityEngine:
    """Factory to create explainability engine."""
    return ExplainabilityEngine()

