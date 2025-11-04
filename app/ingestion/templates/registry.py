"""
Template Registry
=================

Load, validate, and match bank statement templates.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from functools import lru_cache

import yaml
from pydantic import ValidationError

from app.ingestion.templates.schema import (
    BankTemplate,
    TemplateMatchResult
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Registry for bank statement templates.
    
    Loads templates from YAML files and provides matching functionality.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize registry.
        
        Args:
            templates_dir: Directory containing template YAML files.
                          Defaults to app/ingestion/templates/banks/
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "banks"
        
        self.templates_dir = Path(templates_dir)
        self.templates: List[BankTemplate] = []
        self._load_templates()
    
    def _load_templates(self):
        """Load all template YAML files from the templates directory."""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        yaml_files = list(self.templates_dir.glob("*.yaml")) + list(self.templates_dir.glob("*.yml"))
        
        if not yaml_files:
            logger.warning(f"No YAML files found in {self.templates_dir}")
            return
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                template = BankTemplate(**data)
                self.templates.append(template)
                logger.info(f"Loaded template: {template.name} v{template.version} from {yaml_file.name}")
            
            except ValidationError as e:
                logger.error(f"Validation error loading {yaml_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error loading template from {yaml_file.name}: {e}")
        
        logger.info(f"Loaded {len(self.templates)} templates")
    
    def match_pdf(self, features: Dict) -> List[TemplateMatchResult]:
        """
        Match PDF features against all templates.
        
        Args:
            features: Dictionary of extracted features from PDF
                     (from text_features.extract_text_features())
        
        Returns:
            List of TemplateMatchResult, sorted by score (descending)
        """
        results = []
        
        for template in self.templates:
            score, component_scores, matched_tokens = self._score_template(template, features)
            
            result = TemplateMatchResult(
                template=template,
                score=score,
                component_scores=component_scores,
                matched_tokens=matched_tokens,
                confidence=score  # For now, confidence equals score
            )
            
            results.append(result)
        
        # Sort by score descending
        results.sort()
        
        return results
    
    def get_best_match(self, features: Dict) -> Optional[TemplateMatchResult]:
        """
        Get the best matching template for given features.
        
        Args:
            features: Dictionary of extracted features from PDF
        
        Returns:
            Best TemplateMatchResult or None if no template meets threshold
        """
        matches = self.match_pdf(features)
        
        if not matches:
            return None
        
        best = matches[0]
        
        if best.score >= best.template.accept_threshold:
            logger.info(
                f"Best match: {best.template.name} "
                f"(score: {best.score:.3f}, threshold: {best.template.accept_threshold:.3f})"
            )
            return best
        else:
            logger.info(
                f"Best match {best.template.name} score {best.score:.3f} "
                f"below threshold {best.template.accept_threshold:.3f}"
            )
            return None
    
    def _score_template(
        self,
        template: BankTemplate,
        features: Dict
    ) -> Tuple[float, Dict[str, float], Dict[str, List[str]]]:
        """
        Score a template against features.
        
        Args:
            template: BankTemplate to score
            features: Extracted features
        
        Returns:
            Tuple of (overall_score, component_scores, matched_tokens)
        """
        component_scores = {}
        matched_tokens = {
            'headers': [],
            'table': [],
            'footer': []
        }
        
        # Score header keywords
        header_score = self._score_keywords(
            template.match.header_keys,
            features.get('header_text', ''),
            matched_tokens['headers']
        )
        component_scores['headers'] = header_score
        
        # Score table headers
        table_score = self._score_table_headers(
            template.match.table_headers,
            features.get('table_headers', []),
            matched_tokens['table']
        )
        component_scores['table'] = table_score
        
        # Score footer keywords
        footer_score = self._score_keywords(
            template.match.footer_keywords,
            features.get('footer_text', ''),
            matched_tokens['footer']
        )
        component_scores['footer'] = footer_score
        
        # Score geometry
        geometry_score = self._score_geometry(
            template.match.geometry_hints,
            features.get('geometry', {})
        )
        component_scores['geometry'] = geometry_score
        
        # Compute weighted overall score
        weights = template.score_weights
        overall_score = (
            header_score * weights.headers +
            table_score * weights.table +
            footer_score * weights.footer +
            geometry_score * weights.geometry
        )
        
        return overall_score, component_scores, matched_tokens
    
    def _score_keywords(
        self,
        keywords: List[str],
        text: str,
        matched: List[str]
    ) -> float:
        """
        Score keyword presence in text.
        
        Args:
            keywords: List of keywords to find
            text: Text to search in
            matched: List to populate with matched keywords
        
        Returns:
            Score between 0 and 1
        """
        if not keywords:
            return 1.0  # No requirements = perfect score
        
        text_lower = text.lower()
        match_count = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                match_count += 1
                matched.append(keyword)
        
        return match_count / len(keywords)
    
    def _score_table_headers(
        self,
        patterns: List[str],
        detected_headers: List[List[str]],
        matched: List[str]
    ) -> float:
        """
        Score table header patterns against detected headers.
        
        Args:
            patterns: List of regex patterns
            detected_headers: List of detected header rows (list of lists)
            matched: List to populate with matched headers
        
        Returns:
            Score between 0 and 1
        """
        if not patterns:
            return 1.0  # No requirements = perfect score
        
        if not detected_headers:
            return 0.0  # Required but not found
        
        # Flatten detected headers
        all_headers = []
        for row in detected_headers:
            all_headers.extend([str(h).strip() for h in row if h])
        
        if not all_headers:
            return 0.0
        
        match_count = 0
        
        for pattern in patterns:
            try:
                regex = re.compile(pattern)
                for header in all_headers:
                    if regex.match(header):
                        match_count += 1
                        matched.append(f"{header} (pattern: {pattern})")
                        break  # Count each pattern once
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
        
        return match_count / len(patterns)
    
    def _score_geometry(
        self,
        expected: Dict[str, List[float]],
        actual: Dict
    ) -> float:
        """
        Score geometry/layout match.
        
        Args:
            expected: Expected geometry hints from template
            actual: Actual geometry from features
        
        Returns:
            Score between 0 and 1
        """
        if not expected or not actual:
            return 0.5  # Neutral score if no geometry data
        
        scores = []
        
        # Check header band
        if 'header_top_pct' in expected and 'header_band' in actual:
            expected_band = expected['header_top_pct']
            actual_band = actual['header_band']
            
            # Check overlap
            overlap = self._compute_band_overlap(expected_band, actual_band)
            scores.append(overlap)
        
        # Check table band
        if 'table_band_pct' in expected and 'table_band' in actual:
            expected_band = expected['table_band_pct']
            actual_band = actual['table_band']
            
            overlap = self._compute_band_overlap(expected_band, actual_band)
            scores.append(overlap)
        
        if not scores:
            return 0.5  # Neutral if no comparable geometry
        
        return sum(scores) / len(scores)
    
    def _compute_band_overlap(self, expected: List[float], actual: List[float]) -> float:
        """
        Compute overlap between two bands (ranges).
        
        Args:
            expected: [start, end] percentages
            actual: [start, end] percentages
        
        Returns:
            Overlap score between 0 and 1
        """
        exp_start, exp_end = expected
        act_start, act_end = actual
        
        # Compute intersection
        intersect_start = max(exp_start, act_start)
        intersect_end = min(exp_end, act_end)
        
        if intersect_start >= intersect_end:
            return 0.0  # No overlap
        
        intersect_length = intersect_end - intersect_start
        
        # Compute union
        union_start = min(exp_start, act_start)
        union_end = max(exp_end, act_end)
        union_length = union_end - union_start
        
        if union_length == 0:
            return 1.0
        
        # IoU (Intersection over Union)
        return intersect_length / union_length
    
    def get_template_by_name(self, name: str) -> Optional[BankTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Template name
        
        Returns:
            BankTemplate or None
        """
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def reload(self):
        """Reload all templates from disk."""
        self.templates = []
        self._load_templates()
    
    def __len__(self):
        """Return number of loaded templates."""
        return len(self.templates)
    
    def __repr__(self):
        return f"TemplateRegistry({len(self.templates)} templates loaded)"


@lru_cache(maxsize=1)
def get_default_registry() -> TemplateRegistry:
    """
    Get the default template registry (cached).
    
    Returns:
        TemplateRegistry instance
    """
    return TemplateRegistry()



