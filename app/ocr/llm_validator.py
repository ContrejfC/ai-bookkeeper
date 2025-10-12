"""
LLM Validator for low-confidence OCR fields.

Provider-agnostic interface supporting OpenAI, Anthropic, or custom LLMs.
"""
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def validate_fields(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Validate/correct OCR fields using LLM.
        
        Args:
            raw_text: Raw OCR text
            fields: Extracted fields with confidence scores
            
        Returns:
            Updated fields dict with possibly corrected values and confidence hints
        """
        pass


class OpenAIValidator(LLMProvider):
    """OpenAI-based LLM validator."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI validator.
        
        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
        """
        self.api_key = api_key
        self.model = model
        
        if not api_key:
            logger.warning("OpenAI API key not provided - validator will be disabled")
    
    def validate_fields(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Validate fields using OpenAI API."""
        if not self.api_key:
            logger.warning("OpenAI API key not set - skipping LLM validation")
            return fields
        
        try:
            import openai
            
            # Build prompt
            prompt = self._build_validation_prompt(raw_text, fields)
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at validating and correcting OCR-extracted receipt data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=512
            )
            
            # Parse response
            result = response.choices[0].message.content
            updated_fields = self._parse_llm_response(result, fields)
            
            logger.info(f"LLM validation completed - updated {len(updated_fields)} fields")
            return updated_fields
            
        except ImportError:
            logger.error("openai package not installed - install with: pip install openai")
            return fields
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return fields
    
    def _build_validation_prompt(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> str:
        """Build validation prompt for LLM."""
        prompt = f"""I have OCR text from a receipt and extracted the following fields. 
Please validate and correct any errors.

OCR Text:
```
{raw_text[:1000]}  # Limit to first 1000 chars
```

Extracted Fields:
"""
        for field_name, field_data in fields.items():
            value = field_data.get('value', 'N/A')
            confidence = field_data.get('confidence', 0.0)
            prompt += f"- {field_name}: {value} (confidence: {confidence:.2f})\n"
        
        prompt += """
Please respond in JSON format with corrected values and confidence adjustments:
{
  "vendor": {"value": "...", "confidence_adjustment": 0.1},
  "amount": {"value": 123.45, "confidence_adjustment": 0.05},
  "date": {"value": "2025-10-08", "confidence_adjustment": 0.0},
  "category": {"value": "...", "confidence_adjustment": 0.15}
}

Only include fields that need corrections. Use confidence_adjustment to indicate how much to boost/lower confidence (-0.2 to +0.2).
"""
        return prompt
    
    def _parse_llm_response(self, response: str, original_fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Parse LLM response and update fields."""
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            logger.warning("No JSON found in LLM response")
            return original_fields
        
        try:
            corrections = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            return original_fields
        
        # Apply corrections
        updated_fields = original_fields.copy()
        for field_name, correction in corrections.items():
            if field_name in updated_fields:
                # Update value if provided
                if 'value' in correction:
                    updated_fields[field_name]['value'] = correction['value']
                
                # Adjust confidence
                if 'confidence_adjustment' in correction:
                    adjustment = correction['confidence_adjustment']
                    current_conf = updated_fields[field_name].get('confidence', 0.0)
                    new_conf = max(0.0, min(1.0, current_conf + adjustment))
                    updated_fields[field_name]['confidence'] = new_conf
                    
                    logger.info(
                        f"LLM adjusted {field_name}: "
                        f"confidence {current_conf:.2f} → {new_conf:.2f}"
                    )
        
        return updated_fields


class AnthropicValidator(LLMProvider):
    """Anthropic Claude-based LLM validator (stub)."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        logger.warning("Anthropic validator not fully implemented - using stub")
    
    def validate_fields(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Validate fields using Anthropic API (stub)."""
        logger.warning("Anthropic validation not implemented")
        return fields


class DisabledValidator(LLMProvider):
    """Disabled/no-op validator when LLM validation is turned off."""
    
    def validate_fields(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """No-op validation."""
        logger.debug("LLM validation disabled")
        return fields


class LLMValidator:
    """
    Main LLM validator with provider abstraction.
    
    Supports multiple LLM providers (OpenAI, Anthropic, etc.) and gracefully
    handles missing API keys.
    """
    
    def __init__(self, provider: str = "openai", api_key: str = "", model: str = "gpt-4"):
        """
        Initialize LLM validator.
        
        Args:
            provider: LLM provider (openai, anthropic, disabled)
            api_key: API key for provider
            model: Model name
        """
        self.provider_name = provider.lower()
        
        if provider == "disabled" or not api_key:
            self.provider = DisabledValidator()
            logger.info("LLM validation disabled")
        elif provider == "openai":
            self.provider = OpenAIValidator(api_key, model)
            logger.info(f"LLM validation enabled (OpenAI {model})")
        elif provider == "anthropic":
            self.provider = AnthropicValidator(api_key, model)
            logger.info(f"LLM validation enabled (Anthropic {model})")
        else:
            logger.warning(f"Unknown provider '{provider}' - disabling LLM validation")
            self.provider = DisabledValidator()
    
    def validate(self, raw_text: str, fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Validate/correct OCR fields using LLM.
        
        Args:
            raw_text: Raw OCR text
            fields: Extracted fields with confidence scores
            
        Returns:
            Updated fields dict
        """
        return self.provider.validate_fields(raw_text, fields)
    
    def is_enabled(self) -> bool:
        """Check if LLM validation is enabled."""
        return not isinstance(self.provider, DisabledValidator)


def create_validator_from_settings(settings: Any) -> LLMValidator:
    """
    Create LLM validator from settings object.
    
    Args:
        settings: Settings object with LLM configuration
        
    Returns:
        LLMValidator instance
    """
    llm_enabled = getattr(settings, 'LLM_VALIDATION_ENABLED', False)
    
    if not llm_enabled or llm_enabled == 'false':
        return LLMValidator(provider="disabled")
    
    provider = getattr(settings, 'LLM_PROVIDER', 'openai')
    api_key = getattr(settings, 'OPENAI_API_KEY', '') if provider == 'openai' else getattr(settings, 'LLM_API_KEY', '')
    model = getattr(settings, 'llm_model', 'gpt-4')
    
    return LLMValidator(provider=provider, api_key=api_key, model=model)

