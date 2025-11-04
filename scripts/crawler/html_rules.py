"""
HTML Link Filtering with Category Awareness
==========================================

Smart link scoring and filtering based on institution category and keywords.
Prioritizes links that are more likely to contain statement samples or documentation.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

# Category-specific URL patterns that indicate high-value targets
CATEGORY_PATTERNS = {
    "banks": [
        r"/statement",
        r"/e-?statement",
        r"/paperless",
        r"/online-banking",
        r"/help.*statement",
        r"/support.*statement",
        r"/resources.*statement",
    ],
    "brokerages": [
        r"/statement",
        r"/account-statement",
        r"/trade-confirm",
        r"/monthly-statement",
        r"/quarterly-statement",
        r"/understanding.*statement",
    ],
    "merchants": [
        r"/merchant",
        r"/settlement",
        r"/payout",
        r"/reports",
        r"/analytics",
        r"/transaction-report",
    ],
    "marketplaces": [
        r"/seller",
        r"/payout",
        r"/earnings",
        r"/reports",
        r"/finances",
        r"/statements",
    ],
    "gig": [
        r"/earnings",
        r"/driver.*statement",
        r"/dasher.*statement",
        r"/pay.*statement",
        r"/trip.*statement",
    ],
    "accounting": [
        r"/import",
        r"/bank.*statement",
        r"/reconcil",
        r"/connect",
        r"/feed",
        r"/supported.*format",
        r"/file.*format",
    ],
    "standards": [
        r"/iso.*20022",
        r"/camt",
        r"/mt940",
        r"/bai",
        r"/ofx",
        r"/standard",
        r"/message.*definition",
        r"/download",
    ],
    "crypto": [
        r"/tax",
        r"/report",
        r"/history",
        r"/export",
        r"/transaction.*history",
    ],
}

# High-value file extensions in URL paths
VALUABLE_EXTENSIONS = {
    ".pdf": 100,
    ".csv": 80,
    ".xml": 80,
    ".ofx": 90,
    ".qfx": 90,
    ".qbo": 85,
    ".txt": 60,
    ".xls": 70,
    ".xlsx": 70,
}

# URL patterns to always skip
SKIP_PATTERNS = [
    r"/login",
    r"/signin",
    r"/signup",
    r"/register",
    r"/auth",
    r"/oauth",
    r"/api/",  # API endpoints (unless it's /api/docs)
    r"/checkout",
    r"/cart",
    r"/images?/",
    r"/img/",
    r"/css/",
    r"/js/",
    r"/javascript/",
    r"/assets/",
    r"/static/",
    r"/media/",
    r"/fonts?/",
    r"\.(jpg|jpeg|png|gif|svg|ico|woff|woff2|ttf|eot)$",
    r"#",  # Fragment identifiers
    r"mailto:",
    r"tel:",
    r"javascript:",
]


def categorize_domain(domain: str) -> str:
    """
    Determine the category of a domain based on its name.
    
    Returns: "banks", "brokerages", "merchants", "marketplaces", "gig",
             "accounting", "standards", "crypto", or "general"
    """
    domain_lower = domain.lower()
    
    # Banks (including credit unions)
    bank_keywords = ["bank", "fcu", "credit union", "federal", "savings"]
    if any(kw in domain_lower for kw in bank_keywords):
        return "banks"
    
    # Brokerages
    brokerage_keywords = ["fidelity", "schwab", "etrade", "tdameritrade", "vanguard", 
                         "robinhood", "webull", "merrill", "morgan stanley", "ubs"]
    if any(kw in domain_lower for kw in brokerage_keywords):
        return "brokerages"
    
    # Merchants/Payment processors
    merchant_keywords = ["stripe", "square", "paypal", "braintree", "adyen"]
    if any(kw in domain_lower for kw in merchant_keywords):
        return "merchants"
    
    # Marketplaces
    marketplace_keywords = ["amazon", "ebay", "etsy", "shopify"]
    if any(kw in domain_lower for kw in marketplace_keywords):
        return "marketplaces"
    
    # Gig platforms
    gig_keywords = ["uber", "lyft", "doordash", "instacart"]
    if any(kw in domain_lower for kw in gig_keywords):
        return "gig"
    
    # Accounting/ERP
    accounting_keywords = ["intuit", "quickbooks", "xero", "sage", "wave", "zoho",
                          "plaid", "yodlee", "finicity"]
    if any(kw in domain_lower for kw in accounting_keywords):
        return "accounting"
    
    # Standards bodies
    standards_keywords = ["iso20022", "swift", "ofx.net", "bai.org"]
    if any(kw in domain_lower for kw in standards_keywords):
        return "standards"
    
    # Crypto
    crypto_keywords = ["coinbase", "kraken", "gemini", "binance"]
    if any(kw in domain_lower for kw in crypto_keywords):
        return "crypto"
    
    return "general"


def score_url(
    url: str,
    base_url: str,
    keyword_allow: List[str],
    keyword_deny: List[str],
    category: Optional[str] = None
) -> Tuple[int, str]:
    """
    Score a URL for relevance to statement/document discovery.
    
    Args:
        url: The URL to score
        base_url: The base URL (for context)
        keyword_allow: List of allowed keywords
        keyword_deny: List of denied keywords
        category: Institution category (optional, will auto-detect if None)
        
    Returns:
        Tuple of (score, reason)
        score: 0-100, higher is better. 0 means skip.
        reason: String explaining the score
    """
    url_lower = url.lower()
    path = urlparse(url).path.lower()
    
    # Check skip patterns first
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, url_lower):
            return 0, f"Skip pattern: {pattern}"
    
    score = 50  # Base score
    reasons = []
    
    # Check for valuable file extensions
    for ext, ext_score in VALUABLE_EXTENSIONS.items():
        if url_lower.endswith(ext):
            score += ext_score
            reasons.append(f"Valuable extension: {ext} (+{ext_score})")
            break
    
    # Check keyword deny list (strong negative)
    for keyword in keyword_deny:
        if keyword.lower() in url_lower:
            return 0, f"Denied keyword: {keyword}"
    
    # Check keyword allow list
    keyword_matches = []
    for keyword in keyword_allow:
        if keyword.lower() in url_lower:
            score += 15
            keyword_matches.append(keyword)
    
    if keyword_matches:
        reasons.append(f"Keywords: {', '.join(keyword_matches[:3])} (+{len(keyword_matches)*15})")
    
    # Category-specific patterns
    if not category:
        domain = urlparse(url).netloc
        category = categorize_domain(domain)
    
    if category in CATEGORY_PATTERNS:
        for pattern in CATEGORY_PATTERNS[category]:
            if re.search(pattern, path):
                score += 20
                reasons.append(f"Category pattern ({category}): {pattern} (+20)")
                break
    
    # Prefer shorter paths (usually more general/documentation)
    path_depth = len([p for p in path.split("/") if p])
    if path_depth <= 3:
        score += 10
        reasons.append(f"Shallow path depth: {path_depth} (+10)")
    elif path_depth > 6:
        score -= 10
        reasons.append(f"Deep path depth: {path_depth} (-10)")
    
    # Bonus for specific statement-related words in path
    statement_words = ["statement", "report", "document", "sample", "example", "guide"]
    for word in statement_words:
        if word in path:
            score += 10
            reasons.append(f"Statement word: {word} (+10)")
    
    # Cap score
    score = max(0, min(100, score))
    
    reason_str = "; ".join(reasons) if reasons else "base score"
    return score, reason_str


def filter_links(
    links: List[str],
    base_url: str,
    visited: Set[str],
    keyword_allow: List[str],
    keyword_deny: List[str],
    category: Optional[str] = None,
    max_links: int = 100
) -> List[Tuple[str, int]]:
    """
    Filter and score a list of links, returning the top-scoring ones.
    
    Args:
        links: List of URLs to filter
        base_url: Base URL for context
        visited: Set of already-visited URLs
        keyword_allow: List of allowed keywords
        keyword_deny: List of denied keywords
        category: Institution category
        max_links: Maximum number of links to return
        
    Returns:
        List of (url, score) tuples, sorted by score descending
    """
    scored_links = []
    
    for link in links:
        # Normalize URL
        normalized = urljoin(base_url, link)
        
        # Skip if already visited
        if normalized in visited:
            continue
        
        # Score the link
        score, reason = score_url(normalized, base_url, keyword_allow, keyword_deny, category)
        
        if score > 0:
            scored_links.append((normalized, score, reason))
            logger.debug(f"Scored {normalized}: {score} - {reason}")
    
    # Sort by score descending
    scored_links.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    return [(url, score) for url, score, reason in scored_links[:max_links]]


def should_follow_link(url: str, keyword_allow: List[str], keyword_deny: List[str]) -> Tuple[bool, str]:
    """
    Quick check if a link should be followed at all.
    
    Returns:
        Tuple of (should_follow, reason)
    """
    score, reason = score_url(url, url, keyword_allow, keyword_deny)
    return score > 0, reason


# Example usage
if __name__ == "__main__":
    # Test categorization
    test_domains = [
        "chase.com",
        "fidelity.com",
        "stripe.com",
        "amazon.com",
        "uber.com",
        "quickbooks.intuit.com",
        "swift.com",
        "coinbase.com",
    ]
    
    print("=== Domain Categorization ===")
    for domain in test_domains:
        category = categorize_domain(domain)
        print(f"{domain}: {category}")
    
    # Test URL scoring
    test_urls = [
        "https://www.chase.com/personal/online-banking/statements-documents",
        "https://www.chase.com/login",
        "https://www.fidelity.com/customer-service/statements-confirmations",
        "https://stripe.com/docs/reports/balance.pdf",
        "https://help.uber.com/earnings-statement.pdf",
        "https://www.example.com/images/logo.png",
    ]
    
    print("\n=== URL Scoring ===")
    keyword_allow = ["statement", "report", "earnings", "balance", "sample"]
    keyword_deny = ["login", "privacy", "terms"]
    
    for url in test_urls:
        score, reason = score_url(url, url, keyword_allow, keyword_deny)
        print(f"\n{url}")
        print(f"  Score: {score}")
        print(f"  Reason: {reason}")

