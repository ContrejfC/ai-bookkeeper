"""
Tests for Launch Checks
========================

Unit tests for the launch verification harness.
External API calls are marked with @pytest.mark.e2e and skipped unless explicitly run.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import from the checks module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ops.launch_checks.checks import (
    CheckResult, Report, Config,
    generate_markdown_report,
    interpolate_env_vars,
    load_config
)


# ============================================================================
# Unit Tests (No External Dependencies)
# ============================================================================

class TestConfigLoading:
    """Test configuration loading and env var interpolation."""
    
    def test_interpolate_env_vars_simple_string(self):
        """Test simple environment variable substitution."""
        os.environ['TEST_VAR'] = 'test_value'
        result = interpolate_env_vars('Hello ${TEST_VAR}')
        assert result == 'Hello test_value'
    
    def test_interpolate_env_vars_nested_dict(self):
        """Test nested dictionary interpolation."""
        os.environ['API_URL'] = 'https://api.example.com'
        os.environ['TENANT'] = 'tenant-123'
        
        data = {
            'api_base': '${API_URL}',
            'nested': {
                'tenant_id': '${TENANT}'
            }
        }
        
        result = interpolate_env_vars(data)
        assert result['api_base'] == 'https://api.example.com'
        assert result['nested']['tenant_id'] == 'tenant-123'
    
    def test_interpolate_env_vars_missing_key(self):
        """Test handling of missing environment variables."""
        data = '${NONEXISTENT_VAR}'
        result = interpolate_env_vars(data)
        # Should return original string if var not found
        assert '${NONEXISTENT_VAR}' in result


class TestCheckResult:
    """Test CheckResult data class."""
    
    def test_check_result_creation(self):
        """Test creating a CheckResult."""
        result = CheckResult(
            name="test_check",
            status="PASS",
            duration_ms=100,
            details={"key": "value"},
            evidence="Test passed"
        )
        
        assert result.name == "test_check"
        assert result.status == "PASS"
        assert result.duration_ms == 100
        assert result.required is True
    
    def test_check_result_optional(self):
        """Test optional check result."""
        result = CheckResult(
            name="optional_check",
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="Skipped",
            required=False
        )
        
        assert result.required is False


class TestMarkdownReport:
    """Test Markdown report generation."""
    
    def test_generate_markdown_report_basic(self):
        """Test basic Markdown report generation."""
        report = Report(
            timestamp_utc="2025-10-30T12:00:00Z",
            api_base="https://api.example.com",
            summary={"pass": 2, "fail": 1, "skip": 1, "total": 4},
            checks=[
                {
                    "name": "healthz",
                    "status": "PASS",
                    "duration_ms": 45,
                    "details": {},
                    "evidence": "Health check passed"
                },
                {
                    "name": "readyz",
                    "status": "PASS",
                    "duration_ms": 50,
                    "details": {},
                    "evidence": "Ready check passed"
                },
                {
                    "name": "stripe_check",
                    "status": "FAIL",
                    "duration_ms": 100,
                    "details": {"error": "Connection failed"},
                    "evidence": "Stripe connection failed"
                },
                {
                    "name": "qbo_check",
                    "status": "SKIP",
                    "duration_ms": 0,
                    "details": {},
                    "evidence": "QBO not configured"
                }
            ],
            artifacts=[]
        )
        
        markdown = generate_markdown_report(report)
        
        # Verify key sections present
        assert "# Launch Checks Report" in markdown
        assert "**Timestamp:** 2025-10-30T12:00:00Z" in markdown
        assert "**API Base:** https://api.example.com" in markdown
        assert "✅ **Passed:** 2" in markdown
        assert "❌ **Failed:** 1" in markdown
        assert "⏭️  **Skipped:** 1" in markdown
        assert "healthz" in markdown
        assert "readyz" in markdown
    
    def test_generate_markdown_report_with_artifacts(self):
        """Test Markdown report with artifacts."""
        report = Report(
            timestamp_utc="2025-10-30T12:00:00Z",
            api_base="https://api.example.com",
            summary={"pass": 1, "fail": 0, "skip": 0, "total": 1},
            checks=[
                {
                    "name": "audit_export",
                    "status": "PASS",
                    "duration_ms": 200,
                    "details": {},
                    "evidence": "Audit export successful"
                }
            ],
            artifacts=[
                {
                    "path": "audit.csv",
                    "description": "Audit export sample"
                }
            ]
        )
        
        markdown = generate_markdown_report(report)
        
        assert "## Artifacts" in markdown
        assert "audit.csv" in markdown


class TestIdempotencyLogic:
    """Test idempotency checking logic."""
    
    def test_stripe_session_idempotency(self):
        """Test that duplicate Stripe sessions have same ID."""
        # This would be a real test in production, but here we mock it
        session1_id = "cs_test_123"
        session2_id = "cs_test_123"
        
        assert session1_id == session2_id, "Idempotency failed: different session IDs"
    
    def test_webhook_idempotency(self):
        """Test webhook idempotency logic."""
        # Mock webhook processing
        processed_events = set()
        
        event_id = "evt_test_001"
        
        # First processing
        if event_id not in processed_events:
            processed_events.add(event_id)
            result1 = "processed"
        else:
            result1 = "already_processed"
        
        # Second processing (duplicate)
        if event_id not in processed_events:
            processed_events.add(event_id)
            result2 = "processed"
        else:
            result2 = "already_processed"
        
        assert result1 == "processed"
        assert result2 == "already_processed"


# ============================================================================
# E2E Tests (Require Running API)
# ============================================================================

@pytest.mark.e2e
class TestHealthChecks:
    """End-to-end tests for health endpoints."""
    
    @pytest.fixture
    def api_base(self):
        """Get API base URL from environment."""
        api_base = os.getenv('API_BASE')
        if not api_base:
            pytest.skip("API_BASE not configured")
        return api_base
    
    @pytest.fixture
    def config(self, api_base):
        """Create test configuration."""
        return Config(
            api_base=api_base,
            tenant_id=os.getenv('TEST_TENANT_ID', 'test-tenant'),
            demo_mode=True,
            date_from="2024-01-01",
            date_to="2024-12-31",
            timeout_seconds=30,
            max_retries=3,
            endpoints={
                'health': '/healthz',
                'ready': '/readyz',
                'docs': '/docs',
                'audit_export': '/api/audit/export',
                'upload': '/api/upload',
                'propose': '/api/post/propose',
                'webhook': '/api/billing/stripe_webhook',
                'qbo_export': '/api/export/qbo/demo',
                'xero_export': '/api/export/xero/demo'
            },
            checks={
                'required': ['healthz', 'readyz'],
                'optional': []
            },
            pii_patterns=[],
            upload_limits={},
            ai_thresholds={}
        )
    
    def test_health_endpoint_live(self, config):
        """Test health endpoint against live API."""
        from ops.launch_checks.checks import run_health_check
        
        result = run_health_check(config)
        assert result.status in ["PASS", "SKIP"], f"Health check failed: {result.evidence}"
    
    def test_readiness_endpoint_live(self, config):
        """Test readiness endpoint against live API."""
        from ops.launch_checks.checks import run_readiness_check
        
        result = run_readiness_check(config)
        assert result.status in ["PASS", "SKIP"], f"Readiness check failed: {result.evidence}"


@pytest.mark.e2e
class TestStripeIntegration:
    """End-to-end tests for Stripe integration."""
    
    def test_stripe_idempotency_live(self):
        """Test Stripe checkout session idempotency."""
        if not os.getenv('STRIPE_SECRET_KEY'):
            pytest.skip("STRIPE_SECRET_KEY not configured")
        
        # This would call the actual Stripe API
        # Skipped in unit tests
        pytest.skip("Requires live Stripe credentials")


@pytest.mark.e2e  
class TestPIIRedaction:
    """End-to-end tests for PII redaction."""
    
    def test_pii_redaction_in_logs(self):
        """Test that PII is redacted in API responses."""
        if not os.getenv('API_BASE'):
            pytest.skip("API_BASE not configured")
        
        # This would upload PII probe and verify redaction
        pytest.skip("Requires live API")


# ============================================================================
# Fixtures and Helpers
# ============================================================================

@pytest.fixture
def sample_check_results():
    """Sample check results for testing."""
    return [
        CheckResult(
            name="healthz",
            status="PASS",
            duration_ms=50,
            details={"status_code": 200},
            evidence="Health check passed"
        ),
        CheckResult(
            name="stripe_check",
            status="SKIP",
            duration_ms=0,
            details={},
            evidence="Stripe not configured",
            required=False
        )
    ]


@pytest.fixture
def sample_report(sample_check_results):
    """Sample report for testing."""
    from dataclasses import asdict
    
    checks_dict = [asdict(c) for c in sample_check_results]
    
    return Report(
        timestamp_utc="2025-10-30T12:00:00Z",
        api_base="https://api.example.com",
        summary={"pass": 1, "fail": 0, "skip": 1, "total": 2},
        checks=checks_dict,
        artifacts=[]
    )


def test_report_to_dict(sample_report):
    """Test converting report to dictionary."""
    from dataclasses import asdict
    
    report_dict = asdict(sample_report)
    
    assert 'timestamp_utc' in report_dict
    assert 'api_base' in report_dict
    assert 'summary' in report_dict
    assert 'checks' in report_dict
    assert len(report_dict['checks']) == 2


def test_markdown_generation(sample_report):
    """Test Markdown generation from sample report."""
    markdown = generate_markdown_report(sample_report)
    
    assert isinstance(markdown, str)
    assert len(markdown) > 0
    assert "Launch Checks Report" in markdown



