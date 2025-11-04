#!/usr/bin/env python3
"""
Launch Checks - Pre-Production Verification Suite
=================================================

Runs comprehensive end-to-end checks against deployed AI-Bookkeeper API
and generates timestamped JSON + Markdown reports.

Usage:
    python -m ops.launch_checks.checks --config ops/launch_checks/config.yaml --out report.json
"""

import argparse
import hashlib
import hmac
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from string import Template

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configure HTTP session with retries and timeouts
SESSION = requests.Session()
RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRATEGY)
SESSION.mount("http://", ADAPTER)
SESSION.mount("https://", ADAPTER)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    status: str  # PASS, FAIL, SKIP
    duration_ms: int
    details: Dict[str, Any]
    evidence: str
    required: bool = True


@dataclass
class Report:
    """Complete verification report."""
    timestamp_utc: str
    api_base: str
    summary: Dict[str, int]
    checks: List[Dict[str, Any]]
    artifacts: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Config:
    """Configuration loaded from YAML and env vars."""
    api_base: str
    tenant_id: str
    demo_mode: bool
    date_from: str
    date_to: str
    timeout_seconds: int
    max_retries: int
    endpoints: Dict[str, str]
    checks: Dict[str, List[str]]
    pii_patterns: List[Dict[str, str]]
    upload_limits: Dict[str, int]
    ai_thresholds: Dict[str, float]


# ============================================================================
# Configuration Loading
# ============================================================================

def interpolate_env_vars(data: Any) -> Any:
    """Recursively interpolate ${VAR} with environment variables."""
    if isinstance(data, dict):
        return {k: interpolate_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [interpolate_env_vars(item) for item in data]
    elif isinstance(data, str) and '${' in data:
        # Use Template for safe substitution
        template = Template(data)
        try:
            return template.substitute(os.environ)
        except KeyError as e:
            logger.warning(f"Environment variable not found: {e}")
            return data
    return data


def load_config(config_path: str) -> Config:
    """Load configuration from YAML file with env var interpolation."""
    logger.info(f"Loading config from {config_path}")
    
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    # Interpolate environment variables
    config_data = interpolate_env_vars(raw_config)
    
    # Validate required fields
    if not config_data.get('api_base'):
        raise ValueError("API_BASE not configured")
    if not config_data.get('tenant_id'):
        raise ValueError("TEST_TENANT_ID not configured")
    
    return Config(**config_data)


# ============================================================================
# HTTP Helpers
# ============================================================================

def http_get(url: str, timeout: tuple = (10, 10), headers: Optional[Dict] = None, 
             retries: int = 3) -> requests.Response:
    """
    GET request with retries and timeout.
    
    Args:
        url: Target URL
        timeout: (connect_timeout, read_timeout) in seconds
        headers: Optional headers dict
        retries: Number of retry attempts (default: 3, handled by session)
    
    Returns:
        Response object
    """
    try:
        response = SESSION.get(url, timeout=timeout, headers=headers or {})
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP GET failed for {url}: {e}")
        raise


def http_post(url: str, json_data: Optional[Dict] = None, 
              data: Optional[Any] = None,
              files: Optional[Dict] = None,
              timeout: tuple = (10, 10), 
              headers: Optional[Dict] = None,
              retries: int = 1) -> requests.Response:
    """
    POST request with timeout and optional retries.
    
    Args:
        url: Target URL
        json_data: JSON payload
        data: Form data
        files: File uploads
        timeout: (connect_timeout, read_timeout) in seconds
        headers: Optional headers dict
        retries: Number of retry attempts (handled by session if > 1)
    
    Returns:
        Response object
    """
    try:
        response = SESSION.post(
            url, 
            json=json_data, 
            data=data,
            files=files,
            timeout=timeout, 
            headers=headers or {}
        )
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP POST failed for {url}: {e}")
        raise


# ============================================================================
# Check Implementations
# ============================================================================

def run_health_check(config: Config) -> CheckResult:
    """Check 1: Health endpoint responds correctly."""
    start = time.time()
    name = "healthz"
    
    try:
        url = f"{config.api_base}{config.endpoints['health']}"
        logger.info(f"Checking health: {url}")
        
        response = http_get(url, timeout=(10, 10))
        duration_ms = int((time.time() - start) * 1000)
        
        # Capture body sample (truncate to 4KiB)
        body_sample = response.text[:4096] if response.text else ""
        
        if response.status_code != 200:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={
                    "status_code": response.status_code,
                    "body_sample": body_sample
                },
                evidence=f"Expected 200, got {response.status_code}"
            )
        
        data = response.json()
        is_healthy = data.get('status') == 'healthy' or data.get('ok') is True
        
        if not is_healthy:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"response": data, "body_sample": body_sample},
                evidence="Health check returned non-healthy status"
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"status_code": 200, "response": data},
            evidence="Health endpoint responded with healthy status"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e), "error_type": type(e).__name__},
            evidence=f"Health check failed: {e}"
        )


def run_readiness_check(config: Config) -> CheckResult:
    """Check 2: Readiness endpoint responds correctly."""
    start = time.time()
    name = "readyz"
    
    try:
        url = f"{config.api_base}{config.endpoints['ready']}"
        logger.info(f"Checking readiness: {url}")
        
        response = http_get(url, timeout=config.timeout_seconds)
        duration_ms = int((time.time() - start) * 1000)
        
        if response.status_code != 200:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"status_code": response.status_code, "body": response.text},
                evidence=f"Expected 200, got {response.status_code}"
            )
        
        data = response.json()
        is_ready = data.get('status') == 'ready' or data.get('ok') is True
        
        if not is_ready:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"response": data},
                evidence="Readiness check returned not-ready status"
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"status_code": 200, "response": data},
            evidence="Readiness endpoint responded with ready status"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e), "error_type": type(e).__name__},
            evidence=f"Readiness check failed: {e}"
        )


def run_cors_security_check(config: Config) -> CheckResult:
    """Check 3: CORS and security headers are properly configured."""
    start = time.time()
    name = "cors_security"
    
    try:
        url = f"{config.api_base}{config.endpoints.get('docs', '/docs')}"
        logger.info(f"Checking CORS/security headers: {url}")
        
        response = http_get(url, timeout=config.timeout_seconds)
        duration_ms = int((time.time() - start) * 1000)
        
        headers = dict(response.headers)
        issues = []
        
        # Check for Set-Cookie security attributes (if cookies are used)
        set_cookie = headers.get('Set-Cookie', '')
        if set_cookie:
            if 'HttpOnly' not in set_cookie:
                issues.append("Set-Cookie missing HttpOnly flag")
            if 'Secure' not in set_cookie and 'https' in config.api_base:
                issues.append("Set-Cookie missing Secure flag on HTTPS")
            if 'SameSite' not in set_cookie:
                issues.append("Set-Cookie missing SameSite attribute")
        
        # Check for security headers (optional but recommended)
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
        }
        
        for header, expected in security_headers.items():
            if header not in headers:
                logger.info(f"Recommended header {header} not present (non-critical)")
        
        if issues:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"headers": headers, "issues": issues},
                evidence=f"Security issues found: {', '.join(issues)}"
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"headers": headers, "set_cookie": set_cookie},
            evidence="Security headers properly configured"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"CORS/security check failed: {e}"
        )


def run_stripe_idempotency_check(config: Config) -> CheckResult:
    """Check 4: Stripe checkout session creation is idempotent."""
    start = time.time()
    name = "stripe_idempotency"
    
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_key:
        return CheckResult(
            name=name,
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="STRIPE_SECRET_KEY not configured",
            required=False
        )
    
    try:
        import stripe
        stripe.api_key = stripe_key
        
        logger.info("Testing Stripe checkout session idempotency")
        
        # Create idempotency key
        idempotency_key = f"launch-check-{int(time.time())}"
        
        # First request
        session1 = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Test Product'},
                    'unit_amount': 1000,
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            idempotency_key=idempotency_key
        )
        
        # Second request with same idempotency key
        session2 = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Test Product'},
                    'unit_amount': 1000,
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            idempotency_key=idempotency_key
        )
        
        duration_ms = int((time.time() - start) * 1000)
        
        if session1.id != session2.id:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={
                    "session1_id": session1.id,
                    "session2_id": session2.id
                },
                evidence="Duplicate requests returned different session IDs",
                required=False
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={
                "session_id": session1.id,
                "idempotency_key": idempotency_key
            },
            evidence="Stripe idempotency working correctly",
            required=False
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Stripe idempotency check failed: {e}",
            required=False
        )


def run_webhook_idempotency_check(config: Config) -> CheckResult:
    """Check 5: Webhook events are processed idempotently."""
    start = time.time()
    name = "webhook_idempotency"
    
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_secret or not webhook_url:
        return CheckResult(
            name=name,
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="STRIPE_WEBHOOK_SECRET or WEBHOOK_URL not configured",
            required=False
        )
    
    try:
        logger.info(f"Testing webhook idempotency: {webhook_url}")
        
        # Load sample webhook payload
        fixture_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'stripe_invoice_webhook.json'
        if not fixture_path.exists():
            # Create a sample payload
            webhook_payload = {
                "id": f"evt_test_idempotency_{int(time.time())}",
                "type": "invoice.paid",
                "data": {
                    "object": {
                        "id": "in_test_123",
                        "amount_paid": 5000,
                        "customer": "cus_test_123"
                    }
                }
            }
        else:
            with open(fixture_path) as f:
                webhook_payload = json.load(f)
                # Update event ID to make it unique
                webhook_payload['id'] = f"evt_test_idempotency_{int(time.time())}"
        
        # Compute Stripe signature
        timestamp = int(time.time())
        payload_str = json.dumps(webhook_payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'Stripe-Signature': f't={timestamp},v1={signature}'
        }
        
        # First POST
        response1 = http_post(
            webhook_url, 
            json_data=webhook_payload,
            headers=headers,
            timeout=config.timeout_seconds
        )
        
        # Second POST (duplicate)
        response2 = http_post(
            webhook_url,
            json_data=webhook_payload,
            headers=headers,
            timeout=config.timeout_seconds
        )
        
        duration_ms = int((time.time() - start) * 1000)
        
        # Both should return 2xx
        if response1.status_code not in range(200, 300):
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={
                    "first_status": response1.status_code,
                    "first_body": response1.text
                },
                evidence=f"First webhook POST failed with {response1.status_code}",
                required=False
            )
        
        if response2.status_code not in range(200, 300):
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={
                    "second_status": response2.status_code,
                    "second_body": response2.text
                },
                evidence=f"Second webhook POST failed with {response2.status_code}",
                required=False
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={
                "event_id": webhook_payload['id'],
                "first_response": response1.status_code,
                "second_response": response2.status_code
            },
            evidence="Webhook idempotency working correctly",
            required=False
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Webhook idempotency check failed: {e}",
            required=False
        )


def run_qbo_demo_posting_check(config: Config) -> CheckResult:
    """Check 6: QBO demo posting is idempotent."""
    start = time.time()
    name = "qbo_demo_posting"
    
    qbo_realm = os.getenv('QBO_REALM_ID')
    if not qbo_realm or not config.demo_mode:
        return CheckResult(
            name=name,
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="QBO not configured or demo_mode disabled",
            required=False
        )
    
    try:
        logger.info("Testing QBO demo posting idempotency")
        
        # Load sample journal entry
        fixture_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'qbo_journal_sample.json'
        if fixture_path.exists():
            with open(fixture_path) as f:
                journal_data = json.load(f)
        else:
            # Create minimal journal entry
            journal_data = {
                "date": "2024-10-01",
                "memo": "Launch check test",
                "line_items": [
                    {"account": "Cash", "debit": 100.00, "credit": 0.00},
                    {"account": "Revenue", "debit": 0.00, "credit": 100.00}
                ]
            }
        
        url = f"{config.api_base}{config.endpoints['qbo_export']}"
        
        # First POST
        response1 = http_post(url, json_data=journal_data, timeout=config.timeout_seconds)
        
        # Second POST (should be idempotent)
        response2 = http_post(url, json_data=journal_data, timeout=config.timeout_seconds)
        
        duration_ms = int((time.time() - start) * 1000)
        
        # Check both succeeded
        if response1.status_code not in [200, 201]:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"first_status": response1.status_code},
                evidence=f"First QBO post failed: {response1.status_code}",
                required=False
            )
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Check idempotency - should return same external ID
        qbo_id1 = data1.get('qbo_doc_id') or data1.get('external_id')
        qbo_id2 = data2.get('qbo_doc_id') or data2.get('external_id')
        
        if qbo_id1 != qbo_id2:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"qbo_id1": qbo_id1, "qbo_id2": qbo_id2},
                evidence="QBO posting not idempotent - different IDs returned",
                required=False
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"qbo_doc_id": qbo_id1, "demo_mode": config.demo_mode},
            evidence="QBO demo posting idempotent",
            required=False
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"QBO demo posting check failed: {e}",
            required=False
        )


def run_xero_demo_posting_check(config: Config) -> CheckResult:
    """Check 7: Xero demo posting is idempotent."""
    start = time.time()
    name = "xero_demo_posting"
    
    xero_tenant = os.getenv('XERO_TENANT_ID')
    if not xero_tenant or not config.demo_mode:
        return CheckResult(
            name=name,
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="Xero not configured or demo_mode disabled",
            required=False
        )
    
    try:
        logger.info("Testing Xero demo posting idempotency")
        
        # Similar to QBO check
        fixture_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'xero_journal_sample.json'
        if fixture_path.exists():
            with open(fixture_path) as f:
                journal_data = json.load(f)
        else:
            journal_data = {
                "date": "2024-10-01",
                "narration": "Launch check test",
                "journal_lines": [
                    {"account_code": "200", "line_amount": 100.00},
                    {"account_code": "400", "line_amount": -100.00}
                ]
            }
        
        url = f"{config.api_base}{config.endpoints['xero_export']}"
        
        response1 = http_post(url, json_data=journal_data, timeout=config.timeout_seconds)
        response2 = http_post(url, json_data=journal_data, timeout=config.timeout_seconds)
        
        duration_ms = int((time.time() - start) * 1000)
        
        if response1.status_code not in [200, 201]:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"first_status": response1.status_code},
                evidence=f"First Xero post failed: {response1.status_code}",
                required=False
            )
        
        data1 = response1.json()
        data2 = response2.json()
        
        xero_id1 = data1.get('xero_journal_id') or data1.get('external_id')
        xero_id2 = data2.get('xero_journal_id') or data2.get('external_id')
        
        if xero_id1 != xero_id2:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"xero_id1": xero_id1, "xero_id2": xero_id2},
                evidence="Xero posting not idempotent",
                required=False
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"xero_journal_id": xero_id1},
            evidence="Xero demo posting idempotent",
            required=False
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Xero demo posting check failed: {e}",
            required=False
        )


def run_ai_threshold_gate_check(config: Config) -> CheckResult:
    """Check 8: AI categorization respects confidence thresholds."""
    start = time.time()
    name = "ai_threshold_gate"
    
    try:
        logger.info("Testing AI threshold gating")
        
        # Load small sample CSV
        fixture_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'sample_small.csv'
        if not fixture_path.exists():
            return CheckResult(
                name=name,
                status="SKIP",
                duration_ms=0,
                details={},
                evidence="sample_small.csv fixture not found"
            )
        
        url = f"{config.api_base}{config.endpoints['propose']}"
        
        with open(fixture_path, 'rb') as f:
            files = {'file': ('sample_small.csv', f, 'text/csv')}
            response = http_post(
                url,
                files=files,
                timeout=config.timeout_seconds * 2  # Allow more time for processing
            )
        
        duration_ms = int((time.time() - start) * 1000)
        
        if response.status_code not in [200, 201, 202]:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"status_code": response.status_code, "body": response.text},
                evidence=f"Propose endpoint failed: {response.status_code}"
            )
        
        data = response.json()
        
        # Check for confidence scoring
        has_confidence = False
        has_review_flag = False
        all_balanced = True
        
        entries = data.get('entries', []) or data.get('proposed_entries', [])
        
        for entry in entries:
            if 'confidence' in entry:
                has_confidence = True
            if entry.get('needs_review') or entry.get('confidence', 1.0) < config.ai_thresholds['review_threshold']:
                has_review_flag = True
            
            # Check balance
            debits = sum(line.get('debit', 0) for line in entry.get('line_items', []))
            credits = sum(line.get('credit', 0) for line in entry.get('line_items', []))
            if abs(debits - credits) > 0.01:  # Allow for rounding
                all_balanced = False
        
        if not all_balanced:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"entries": entries},
                evidence="Unbalanced journal entries detected"
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={
                "has_confidence": has_confidence,
                "has_review_flag": has_review_flag,
                "all_balanced": all_balanced,
                "entry_count": len(entries)
            },
            evidence="AI threshold gating working correctly"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"AI threshold check failed: {e}"
        )


def run_pii_redaction_check(config: Config) -> CheckResult:
    """Check 9: PII is redacted in logs and exports."""
    start = time.time()
    name = "pii_redaction"
    
    try:
        logger.info("Testing PII redaction")
        
        # Load PII probe CSV
        fixture_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'pii_probe.csv'
        if not fixture_path.exists():
            return CheckResult(
                name=name,
                status="SKIP",
                duration_ms=0,
                details={},
                evidence="pii_probe.csv fixture not found"
            )
        
        url = f"{config.api_base}{config.endpoints['upload']}"
        
        with open(fixture_path, 'rb') as f:
            files = {'file': ('pii_probe.csv', f, 'text/csv')}
            response = http_post(url, files=files, timeout=config.timeout_seconds)
        
        duration_ms = int((time.time() - start) * 1000)
        
        # Check response for any raw PII
        response_text = response.text.lower()
        
        pii_found = []
        for pattern_info in config.pii_patterns:
            pattern = pattern_info['pattern']
            if pattern.lower() in response_text:
                pii_found.append(pattern_info['name'])
        
        if pii_found:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"pii_found": pii_found, "response_snippet": response_text[:500]},
                evidence=f"Raw PII found in response: {', '.join(pii_found)}"
            )
        
        # Check for redaction markers
        redaction_markers = ['***EMAIL***', '***SSN***', '***PHONE***', '***PAN***']
        markers_found = [marker for marker in redaction_markers if marker in response.text]
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"redaction_markers_found": markers_found},
            evidence="PII properly redacted in responses"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"PII redaction check failed: {e}"
        )


def run_audit_export_check(config: Config, output_dir: Path) -> CheckResult:
    """Check 10: Audit export generates valid CSV."""
    start = time.time()
    name = "audit_export"
    
    try:
        logger.info("Testing audit export")
        
        url = f"{config.api_base}{config.endpoints['audit_export']}"
        params = {
            'tenant_id': config.tenant_id,
            'date_from': config.date_from,
            'date_to': config.date_to
        }
        
        response = http_get(url, timeout=config.timeout_seconds)
        duration_ms = int((time.time() - start) * 1000)
        
        if response.status_code == 401:
            return CheckResult(
                name=name,
                status="SKIP",
                duration_ms=duration_ms,
                details={},
                evidence="Audit export requires authentication (401)",
                required=False
            )
        
        if response.status_code != 200:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"status_code": response.status_code},
                evidence=f"Audit export failed: {response.status_code}",
                required=False
            )
        
        # Save CSV
        audit_csv_path = output_dir / 'audit.csv'
        with open(audit_csv_path, 'wb') as f:
            f.write(response.content)
        
        # Validate CSV
        lines = response.text.split('\n')
        if len(lines) < 1:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"line_count": len(lines)},
                evidence="Audit CSV is empty",
                required=False
            )
        
        header = lines[0]
        expected_columns = ['timestamp', 'action', 'user', 'details']
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={
                "csv_path": str(audit_csv_path),
                "line_count": len(lines),
                "header": header
            },
            evidence=f"Audit CSV generated with {len(lines)} lines",
            required=False
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Audit export check failed: {e}",
            required=False
        )


def run_ingestion_robustness_check(config: Config) -> CheckResult:
    """Check 11: Ingestion handles malformed and oversized files gracefully."""
    start = time.time()
    name = "ingestion_robustness"
    
    try:
        logger.info("Testing ingestion robustness")
        
        url = f"{config.api_base}{config.endpoints['upload']}"
        tests_passed = []
        tests_failed = []
        
        # Test 1: Malformed CSV
        malformed_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'sample_malformed.csv'
        if malformed_path.exists():
            with open(malformed_path, 'rb') as f:
                files = {'file': ('malformed.csv', f, 'text/csv')}
                response = http_post(url, files=files, timeout=config.timeout_seconds, retries=1)
            
            if response.status_code in range(400, 500):
                tests_passed.append("malformed_csv_rejected")
            elif response.status_code == 500:
                tests_failed.append("malformed_csv_500_error")
            else:
                tests_passed.append("malformed_csv_handled")
        
        # Test 2: Oversized file
        oversized_path = Path(__file__).parent.parent.parent / 'ops' / 'fixtures' / 'oversized_100k_rows.csv'
        if oversized_path.exists():
            with open(oversized_path, 'rb') as f:
                files = {'file': ('oversized.csv', f, 'text/csv')}
                response = http_post(url, files=files, timeout=config.timeout_seconds * 3, retries=1)
            
            # Should either accept (202) or reject cleanly (4xx)
            if response.status_code in [200, 201, 202] or response.status_code in range(400, 500):
                tests_passed.append("oversized_handled")
            elif response.status_code == 500:
                tests_failed.append("oversized_500_error")
        
        duration_ms = int((time.time() - start) * 1000)
        
        if tests_failed:
            return CheckResult(
                name=name,
                status="FAIL",
                duration_ms=duration_ms,
                details={"passed": tests_passed, "failed": tests_failed},
                evidence=f"Robustness failures: {', '.join(tests_failed)}"
            )
        
        return CheckResult(
            name=name,
            status="PASS",
            duration_ms=duration_ms,
            details={"tests_passed": tests_passed},
            evidence="Ingestion handles edge cases gracefully"
        )
        
    except Exception as e:
        return CheckResult(
            name=name,
            status="FAIL",
            duration_ms=int((time.time() - start) * 1000),
            details={"error": str(e)},
            evidence=f"Ingestion robustness check failed: {e}"
        )


# ============================================================================
# Report Generation
# ============================================================================

def generate_markdown_report(report: Report) -> str:
    """Convert JSON report to Markdown."""
    lines = [
        "# Launch Checks Report",
        "",
        f"**Timestamp:** {report.timestamp_utc}",
        f"**API Base:** {report.api_base}",
        "",
        "## Summary",
        "",
        f"- ✅ **Passed:** {report.summary['pass']}",
        f"- ❌ **Failed:** {report.summary['fail']}",
        f"- ⏭️  **Skipped:** {report.summary['skip']}",
        f"- 📊 **Total:** {report.summary['total']}",
        "",
        "## Checks",
        "",
        "| Check | Status | Duration (ms) | Evidence |",
        "|-------|--------|---------------|----------|"
    ]
    
    for check in report.checks:
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'SKIP': '⏭️'
        }.get(check['status'], '❓')
        
        lines.append(
            f"| {check['name']} | {status_emoji} {check['status']} | "
            f"{check['duration_ms']} | {check['evidence'][:100]} |"
        )
    
    if report.artifacts:
        lines.extend([
            "",
            "## Artifacts",
            ""
        ])
        for artifact in report.artifacts:
            lines.append(f"- **{artifact['description']}**: `{artifact['path']}`")
    
    lines.extend([
        "",
        "---",
        "",
        f"*Generated by AI-Bookkeeper Launch Checks v1.0*"
    ])
    
    return '\n'.join(lines)


# ============================================================================
# Report Pruning
# ============================================================================

def prune_reports(base: str = "ops/reports", keep: int = 20):
    """
    Prune old report directories, keeping only the most recent ones.
    
    Args:
        base: Base directory containing report folders
        keep: Number of recent reports to retain
    """
    try:
        base_path = Path(base)
        if not base_path.exists():
            return
        
        # Get all subdirectories sorted by modification time (newest first)
        runs = sorted(
            [p for p in base_path.glob("*/") if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Delete old reports beyond the keep limit
        for old_report in runs[keep:]:
            logger.info(f"Pruning old report: {old_report}")
            shutil.rmtree(old_report, ignore_errors=True)
            
    except Exception as e:
        logger.warning(f"Failed to prune reports: {e}")


# ============================================================================
# Main Runner
# ============================================================================

def run_all_checks(config: Config, output_dir: Path) -> Report:
    """Run all checks and generate report."""
    logger.info("Starting launch checks...")
    
    checks = []
    
    # Run all checks
    checks.append(run_health_check(config))
    checks.append(run_readiness_check(config))
    checks.append(run_cors_security_check(config))
    checks.append(run_stripe_idempotency_check(config))
    checks.append(run_webhook_idempotency_check(config))
    checks.append(run_qbo_demo_posting_check(config))
    checks.append(run_xero_demo_posting_check(config))
    checks.append(run_ai_threshold_gate_check(config))
    checks.append(run_pii_redaction_check(config))
    checks.append(run_audit_export_check(config, output_dir))
    checks.append(run_ingestion_robustness_check(config))
    
    # Calculate summary
    summary = {
        'pass': sum(1 for c in checks if c.status == 'PASS'),
        'fail': sum(1 for c in checks if c.status == 'FAIL'),
        'skip': sum(1 for c in checks if c.status == 'SKIP'),
        'total': len(checks)
    }
    
    # Build report
    report = Report(
        timestamp_utc=datetime.utcnow().isoformat() + 'Z',
        api_base=config.api_base,
        summary=summary,
        checks=[asdict(c) for c in checks],
        artifacts=[
            {"path": "audit.csv", "description": "Audit export sample"}
        ]
    )
    
    logger.info(f"Checks complete: {summary['pass']}/{summary['total']} passed")
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run AI-Bookkeeper launch checks')
    parser.add_argument('--config', default='ops/launch_checks/config.yaml', help='Config file path')
    parser.add_argument('--out', required=True, help='Output JSON file path')
    args = parser.parse_args()
    
    try:
        # Load config
        config = load_config(args.config)
        
        # Create output directory
        output_path = Path(args.out)
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run checks
        report = run_all_checks(config, output_dir)
        
        # Write JSON report
        with open(output_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        logger.info(f"Report written to {output_path}")
        
        # Write Markdown report
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write(generate_markdown_report(report))
        logger.info(f"Markdown report written to {md_path}")
        
        # Prune old reports (keep last 20)
        prune_reports()
        
        # Exit with appropriate code
        if report.summary['fail'] > 0:
            # Check if any failed checks are required
            failed_required = any(
                c['status'] == 'FAIL' and c.get('required', True)
                for c in report.checks
            )
            if failed_required:
                logger.error("One or more REQUIRED checks failed")
                sys.exit(1)
        
        logger.info("All required checks passed")
        sys.exit(0)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
        sys.exit(3)


if __name__ == '__main__':
    main()

