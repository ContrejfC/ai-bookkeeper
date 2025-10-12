"""
Vendor name normalization for preventing data leakage (Sprint 9 Stage C).

Ensures consistent vendor keys across train/test splits to prevent
vendor string leakage that could inflate model accuracy.
"""
import re
import string
import unicodedata
from typing import Optional


def normalize_vendor(vendor: str) -> str:
    """
    Normalize vendor name to prevent leakage across train/test.
    
    Steps (enhanced for Stage C):
    1. Unicode/emoji normalize (NFKD decomposition)
    2. Lowercase
    3. Strip punctuation (.,!?;:'"-)
    4. Remove POS prefixes/suffixes (POS PURCHASE, WEB AUTH, etc.)
    5. Strip trailing store numbers & codes (#1234, Store 456, etc.)
    6. Remove corporate stopwords (inc, llc, co, corp, company, ltd)
    7. Collapse multiple whitespace
    8. Strip leading/trailing whitespace
    
    Examples:
        "Office Depot, Inc." → "office depot"
        "WALGREENS #1234" → "walgreens"
        "POS PURCHASE AMAZON.COM" → "amazoncom"
        "Stripe LLC" → "stripe"
        "Café Émoji ☕" → "cafe emoji"
    
    Args:
        vendor: Raw vendor string
        
    Returns:
        Normalized vendor string
    """
    if not vendor:
        return ""
    
    # Step 1: Unicode normalize (NFKD) - handles accents and emojis
    vendor = unicodedata.normalize('NFKD', vendor)
    # Remove non-ASCII characters (emojis become empty after NFKD)
    vendor = vendor.encode('ascii', 'ignore').decode('ascii')
    
    # Step 2: Lowercase
    vendor = vendor.lower()
    
    # Step 3: Strip punctuation
    vendor = vendor.translate(str.maketrans('', '', string.punctuation))
    
    # Step 4: Remove POS prefixes/suffixes
    pos_patterns = [
        r'\bpos\b',
        r'\bpurchase\b',
        r'\bweb\b',
        r'\bauth\b',
        r'\bauthorization\b',
        r'\bdebit\b',
        r'\bcredit\b',
        r'\bcard\b',
        r'\btxn\b',
        r'\btransaction\b',
        r'\bpayment\b',
        r'\bsale\b',
    ]
    for pattern in pos_patterns:
        vendor = re.sub(pattern, '', vendor, flags=re.IGNORECASE)
    
    # Step 5: Strip trailing store numbers & codes
    # Patterns: #1234, Store 456, Location 789, Unit 012, Branch 345
    vendor = re.sub(r'\s*#\s*\d+', '', vendor)  # #1234
    vendor = re.sub(r'\s+store\s+\d+', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+location\s+\d+', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+unit\s+\d+', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+branch\s+\d+', '', vendor, flags=re.IGNORECASE)
    vendor = re.sub(r'\s+\d{3,5}$', '', vendor)  # Trailing 3-5 digit codes
    
    # Step 6: Remove corporate stopwords
    stopwords = [
        'inc', 'llc', 'co', 'corp', 'corporation', 'company', 
        'ltd', 'limited', 'plc', 'sa', 'nv', 'bv', 'gmbh',
        'incorporated', 'dba', 'aka', 'fka'
    ]
    words = vendor.split()
    words = [w for w in words if w not in stopwords]
    vendor = ' '.join(words)
    
    # Step 7: Collapse multiple whitespace
    vendor = re.sub(r'\s+', ' ', vendor)
    
    # Step 8: Strip leading/trailing whitespace
    vendor = vendor.strip()
    
    return vendor


def normalize_vendor_batch(vendors: list[str]) -> list[str]:
    """
    Normalize a batch of vendor names.
    
    Args:
        vendors: List of raw vendor strings
        
    Returns:
        List of normalized vendor strings
    """
    return [normalize_vendor(v) for v in vendors]


# Test examples for validation
_TEST_CASES = {
    "Office Depot, Inc.": "office depot",
    "WALGREENS #1234": "walgreens",
    "POS PURCHASE AMAZON.COM": "amazoncom",
    "Stripe LLC": "stripe",
    "Café Émoji ☕": "cafe emoji",
    "Walmart Store 456": "walmart",
    "TARGET #0789": "target",
    "McDonald's Corp.": "mcdonalds",
    "Starbucks Location 123": "starbucks",
    "CVS/pharmacy #4567": "cvspharmacy",
    "WEB AUTH NETFLIX.COM": "netflixcom",
}


def validate_normalization():
    """Validate normalization against test cases."""
    print("Vendor Normalization Test Cases:")
    print("=" * 80)
    
    all_passed = True
    for raw, expected in _TEST_CASES.items():
        normalized = normalize_vendor(raw)
        passed = normalized == expected
        status = "✅" if passed else "❌"
        
        print(f"{status} {raw:40s} → {normalized:30s} (expected: {expected})")
        
        if not passed:
            all_passed = False
    
    print("=" * 80)
    print(f"Result: {'✅ All passed' if all_passed else '❌ Some failed'}")
    
    return all_passed


if __name__ == "__main__":
    validate_normalization()

