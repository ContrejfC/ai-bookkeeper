"""
Vendor Normalization Rules
==========================

Normalize vendor names using pattern matching and rules.
Supports tenant-specific overrides and global defaults.
"""

import re
import logging
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Default global vendor normalization rules
DEFAULT_VENDOR_RULES = [
    # Cloud & SaaS
    (r'(?i)amazon\s*(web\s*services|aws)', 'Amazon Web Services', False),
    (r'(?i)aws\s*', 'Amazon Web Services', False),
    (r'(?i)google\s*cloud', 'Google Cloud Platform', False),
    (r'(?i)microsoft\s*(azure|office|365)', 'Microsoft', False),
    (r'(?i)salesforce\.com', 'Salesforce', False),
    (r'(?i)slack\s*technolog', 'Slack', False),
    (r'(?i)zoom\.us', 'Zoom', False),
    (r'(?i)dropbox', 'Dropbox', False),
    (r'(?i)github', 'GitHub', False),
    
    # Payment processors
    (r'(?i)stripe\s*(inc|payments)?', 'Stripe', False),
    (r'(?i)paypal', 'PayPal', False),
    (r'(?i)square\s*(inc)?', 'Square', False),
    
    # Common merchants
    (r'(?i)amazon\.com', 'Amazon', False),
    (r'(?i)amzn\s*mktp', 'Amazon Marketplace', False),
    (r'(?i)walmart', 'Walmart', False),
    (r'(?i)target\s*', 'Target', False),
    (r'(?i)costco', 'Costco', False),
    
    # Utilities
    (r'(?i)at&t', 'AT&T', False),
    (r'(?i)verizon', 'Verizon', False),
    (r'(?i)comcast', 'Comcast', False),
    (r'(?i)pg&e', 'PG&E', False),
    
    # Food & beverage
    (r'(?i)starbucks', 'Starbucks', False),
    (r'(?i)mcdonald', 'McDonald\'s', False),
    (r'(?i)uber\s*eats', 'Uber Eats', False),
    (r'(?i)doordash', 'DoorDash', False),
    
    # Transportation
    (r'(?i)uber\s*trip', 'Uber', False),
    (r'(?i)lyft', 'Lyft', False),
    (r'(?i)delta\s*(air|airlines)', 'Delta Air Lines', False),
    (r'(?i)united\s*air', 'United Airlines', False),
    
    # Financial services
    (r'(?i)chase\s*bank', 'Chase', False),
    (r'(?i)wells\s*fargo', 'Wells Fargo', False),
    (r'(?i)bank\s*of\s*america', 'Bank of America', False),
    (r'(?i)citi\s*bank', 'Citibank', False),
]


class VendorNormalizer:
    """
    Normalize vendor names using pattern matching.
    
    Supports:
    - Global default rules
    - Tenant-specific rules (from database)
    - Fuzzy matching
    - Confidence scoring
    """
    
    def __init__(self, db: Optional[Session] = None, tenant_id: Optional[UUID] = None):
        """
        Initialize vendor normalizer.
        
        Args:
            db: Database session (optional)
            tenant_id: Tenant ID for loading custom rules (optional)
        """
        self.db = db
        self.tenant_id = tenant_id
        self.rules: List[Tuple[re.Pattern, str, int]] = []
        
        # Load rules
        self._load_rules()
    
    def _load_rules(self):
        """Load vendor rules from defaults and database."""
        # Load default rules
        for pattern, normalized, _ in DEFAULT_VENDOR_RULES:
            try:
                compiled = re.compile(pattern)
                self.rules.append((compiled, normalized, 100))  # Default priority
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
        
        # Load tenant-specific rules from database
        if self.db and self.tenant_id:
            try:
                from app.ingestion.models import VendorRule
                
                tenant_rules = (
                    self.db.query(VendorRule)
                    .filter(
                        VendorRule.tenant_id == self.tenant_id,
                        VendorRule.active == True
                    )
                    .order_by(VendorRule.priority)
                    .all()
                )
                
                for rule in tenant_rules:
                    try:
                        if rule.is_regex:
                            compiled = re.compile(rule.pattern)
                        else:
                            # Exact match - escape special chars
                            compiled = re.compile(re.escape(rule.pattern), re.IGNORECASE)
                        
                        self.rules.append((compiled, rule.normalized, rule.priority))
                    except re.error as e:
                        logger.error(f"Invalid regex in tenant rule {rule.id}: {e}")
            
            except Exception as e:
                logger.error(f"Failed to load tenant rules: {e}")
        
        # Sort rules by priority (lower = higher priority)
        self.rules.sort(key=lambda x: x[2])
        
        logger.debug(f"Loaded {len(self.rules)} vendor normalization rules")
    
    def normalize(self, vendor: str) -> Tuple[str, float, str]:
        """
        Normalize a vendor name.
        
        Args:
            vendor: Raw vendor name
        
        Returns:
            Tuple of (normalized_name, confidence, method)
        """
        if not vendor or not vendor.strip():
            return vendor, 0.0, "empty"
        
        original = vendor.strip()
        
        # Try pattern matching
        for pattern, normalized, priority in self.rules:
            if pattern.search(original):
                # Confidence based on priority (lower priority = higher confidence)
                confidence = max(0.6, 1.0 - (priority / 1000))
                logger.debug(f"Matched '{original}' -> '{normalized}' (confidence: {confidence:.2f})")
                return normalized, confidence, "pattern"
        
        # No match - clean up the original
        cleaned = self._clean_vendor_name(original)
        
        # If cleaning changed it significantly, return cleaned version
        if cleaned != original:
            return cleaned, 0.5, "cleaned"
        
        # Return original
        return original, 0.3, "none"
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """
        Clean up vendor name by removing common noise.
        
        Args:
            vendor: Raw vendor name
        
        Returns:
            Cleaned vendor name
        """
        if not vendor:
            return vendor
        
        # Remove common prefixes/suffixes
        cleaned = vendor
        
        # Remove trailing location/date info
        cleaned = re.sub(r'\s+\d{2}/\d{2}(/\d{2,4})?\s*$', '', cleaned)  # Remove dates
        cleaned = re.sub(r'\s+[A-Z]{2}\s*$', '', cleaned)  # Remove state codes
        cleaned = re.sub(r'\s+#\d+\s*$', '', cleaned)  # Remove store numbers
        
        # Remove common noise
        noise_patterns = [
            r'(?i)\s*inc\.?$',
            r'(?i)\s*llc\.?$',
            r'(?i)\s*ltd\.?$',
            r'(?i)\s*corp\.?$',
            r'(?i)\s*co\.?$',
            r'\s+\*+\s*',  # Asterisks
            r'\s+\-+\s*',  # Dashes
        ]
        
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Title case for better readability
        cleaned = cleaned.title()
        
        return cleaned.strip()
    
    def bulk_normalize(self, vendors: List[str]) -> List[Tuple[str, str, float, str]]:
        """
        Normalize multiple vendor names.
        
        Args:
            vendors: List of raw vendor names
        
        Returns:
            List of tuples: (original, normalized, confidence, method)
        """
        results = []
        for vendor in vendors:
            normalized, confidence, method = self.normalize(vendor)
            results.append((vendor, normalized, confidence, method))
        return results


def normalize_vendor(vendor: str, db: Optional[Session] = None, tenant_id: Optional[UUID] = None) -> Tuple[str, float]:
    """
    Convenience function to normalize a single vendor name.
    
    Args:
        vendor: Raw vendor name
        db: Database session (optional)
        tenant_id: Tenant ID (optional)
    
    Returns:
        Tuple of (normalized_name, confidence)
    """
    normalizer = VendorNormalizer(db=db, tenant_id=tenant_id)
    normalized, confidence, _ = normalizer.normalize(vendor)
    return normalized, confidence


def add_vendor_rule(
    db: Session,
    tenant_id: UUID,
    pattern: str,
    normalized: str,
    is_regex: bool = False,
    priority: int = 50,
    description: Optional[str] = None
) -> bool:
    """
    Add a new vendor normalization rule.
    
    Args:
        db: Database session
        tenant_id: Tenant ID
        pattern: Pattern to match (regex or exact)
        normalized: Normalized vendor name
        is_regex: Whether pattern is regex
        priority: Rule priority (lower = higher priority)
        description: Optional description
    
    Returns:
        True if rule added successfully
    """
    try:
        from app.ingestion.models import VendorRule
        
        # Validate regex if needed
        if is_regex:
            re.compile(pattern)
        
        rule = VendorRule(
            tenant_id=tenant_id,
            pattern=pattern,
            normalized=normalized,
            is_regex=is_regex,
            priority=priority,
            description=description,
            active=True
        )
        
        db.add(rule)
        db.commit()
        
        logger.info(f"Added vendor rule for tenant {tenant_id}: '{pattern}' -> '{normalized}'")
        return True
    
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        db.rollback()
        return False
    except Exception as e:
        logger.error(f"Failed to add vendor rule: {e}")
        db.rollback()
        return False



