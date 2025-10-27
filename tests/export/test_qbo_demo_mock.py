"""
Test QBO Demo/Mock Export
==========================

Tests for QuickBooks Online demo mode and sandbox support.

Test Cases:
-----------
1. Demo mode returns mock QBO doc ID
2. Demo mode is idempotent
3. Sandbox environment uses correct credentials
4. Production environment uses correct credentials
5. Mock export doesn't call real QBO API
6. Balance validation works
7. Idempotency hash prevents duplicates
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from app.services.qbo import QBOService
from app.integrations.qbo.client import QBOClient, QBO_ENV, DEMO_MODE
from app.db.models import JEIdempotencyDB, DecisionAuditLogDB


@pytest.fixture
def qbo_service(db_session):
    """QBO service fixture."""
    return QBOService(db_session)


@pytest.fixture
def je_payload():
    """Sample journal entry payload."""
    return {
        "txnDate": "2025-10-27",
        "lines": [
            {"account": "5000", "amount": 100, "postingType": "Debit"},
            {"account": "1000", "amount": 100, "postingType": "Credit"}
        ],
        "refNumber": "JE-001",
        "privateNote": "Test journal entry"
    }


@pytest.fixture
def unbalanced_payload():
    """Unbalanced journal entry (should fail validation)."""
    return {
        "txnDate": "2025-10-27",
        "lines": [
            {"account": "5000", "amount": 100, "postingType": "Debit"},
            {"account": "1000", "amount": 50, "postingType": "Credit"}  # Unbalanced!
        ]
    }


@pytest.mark.asyncio
async def test_demo_mode_returns_mock_doc_id(qbo_service, je_payload, db_session):
    """Test that demo mode returns mock QBO doc ID."""
    with patch('app.services.qbo.DEMO_MODE', True):
        result = await qbo_service.post_idempotent_je(
            tenant_id="test-tenant",
            payload=je_payload
        )
        
        assert result["status"] == 201
        assert result["qbo_doc_id"].startswith("mock_")
        assert result["posted_mock"] is True
        assert "DEMO MODE" in result["message"]


@pytest.mark.asyncio
async def test_demo_mode_is_idempotent(qbo_service, je_payload, db_session):
    """Test that demo mode respects idempotency."""
    with patch('app.services.qbo.DEMO_MODE', True):
        # First call
        result1 = await qbo_service.post_idempotent_je(
            tenant_id="test-tenant",
            payload=je_payload
        )
        
        doc_id_1 = result1["qbo_doc_id"]
        
        # Second call with same payload
        result2 = await qbo_service.post_idempotent_je(
            tenant_id="test-tenant",
            payload=je_payload
        )
        
        doc_id_2 = result2["qbo_doc_id"]
        
        # Should return same doc ID
        assert doc_id_1 == doc_id_2
        assert result2["idempotent"] is True
        assert result2["status"] == 200


@pytest.mark.asyncio
async def test_demo_mode_stores_idempotency_record(qbo_service, je_payload, db_session):
    """Test that demo mode stores idempotency records."""
    with patch('app.services.qbo.DEMO_MODE', True):
        result = await qbo_service.post_idempotent_je(
            tenant_id="test-tenant",
            payload=je_payload
        )
        
        # Check idempotency record exists
        payload_hash = qbo_service.compute_payload_hash("test-tenant", je_payload)
        
        record = db_session.query(JEIdempotencyDB).filter_by(
            tenant_id="test-tenant",
            payload_hash=payload_hash
        ).first()
        
        assert record is not None
        assert record.qbo_doc_id == result["qbo_doc_id"]
        assert record.qbo_sync_token == "MOCK"


@pytest.mark.asyncio
async def test_demo_mode_creates_audit_log(qbo_service, je_payload, db_session):
    """Test that demo mode creates audit logs."""
    with patch('app.services.qbo.DEMO_MODE', True):
        await qbo_service.post_idempotent_je(
            tenant_id="test-tenant",
            payload=je_payload
        )
        
        # Check audit log
        audit = db_session.query(DecisionAuditLogDB).filter_by(
            tenant_id="test-tenant",
            action="QBO_JE_POSTED_MOCK"
        ).first()
        
        assert audit is not None


def test_balance_validation_rejects_unbalanced(qbo_service, unbalanced_payload):
    """Test that unbalanced journal entries are rejected."""
    is_valid, error = qbo_service.validate_balance(unbalanced_payload["lines"])
    
    assert is_valid is False
    assert "must equal" in error.lower()


def test_balance_validation_accepts_balanced(qbo_service, je_payload):
    """Test that balanced journal entries pass validation."""
    is_valid, error = qbo_service.validate_balance(je_payload["lines"])
    
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_unbalanced_entry_raises_error(qbo_service, unbalanced_payload):
    """Test that attempting to post unbalanced entry raises ValueError."""
    with patch('app.services.qbo.DEMO_MODE', True):
        with pytest.raises(ValueError) as exc_info:
            await qbo_service.post_idempotent_je(
                tenant_id="test-tenant",
                payload=unbalanced_payload
            )
        
        assert "UNBALANCED_JE" in str(exc_info.value)


def test_payload_hash_is_consistent(qbo_service, je_payload):
    """Test that payload hash is deterministic."""
    hash1 = qbo_service.compute_payload_hash("tenant-1", je_payload)
    hash2 = qbo_service.compute_payload_hash("tenant-1", je_payload)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


def test_payload_hash_differs_by_tenant(qbo_service, je_payload):
    """Test that different tenants get different hashes."""
    hash1 = qbo_service.compute_payload_hash("tenant-1", je_payload)
    hash2 = qbo_service.compute_payload_hash("tenant-2", je_payload)
    
    assert hash1 != hash2


def test_payload_hash_differs_by_content(qbo_service, je_payload):
    """Test that different payloads get different hashes."""
    payload2 = je_payload.copy()
    payload2["refNumber"] = "JE-002"  # Change content
    
    hash1 = qbo_service.compute_payload_hash("tenant-1", je_payload)
    hash2 = qbo_service.compute_payload_hash("tenant-1", payload2)
    
    assert hash1 != hash2


def test_qbo_client_detects_sandbox_environment():
    """Test that QBO client detects sandbox environment."""
    with patch.dict('os.environ', {'QBO_ENV': 'sandbox'}):
        # Reload module to pick up env var
        from importlib import reload
        import app.integrations.qbo.client as client_module
        reload(client_module)
        
        assert client_module.QBO_BASE == "https://sandbox-quickbooks.api.intuit.com"


def test_qbo_client_detects_production_environment():
    """Test that QBO client detects production environment."""
    with patch.dict('os.environ', {'QBO_ENV': 'production'}):
        from importlib import reload
        import app.integrations.qbo.client as client_module
        reload(client_module)
        
        assert client_module.QBO_BASE == "https://quickbooks.api.intuit.com"


def test_qbo_client_uses_sandbox_credentials():
    """Test that sandbox environment uses sandbox credentials."""
    with patch.dict('os.environ', {
        'QBO_ENV': 'sandbox',
        'QBO_CLIENT_ID_SANDBOX': 'sandbox_client_id',
        'QBO_CLIENT_SECRET_SANDBOX': 'sandbox_secret'
    }):
        from importlib import reload
        import app.integrations.qbo.client as client_module
        reload(client_module)
        
        assert client_module.QBO_CLIENT_ID == 'sandbox_client_id'
        assert client_module.QBO_CLIENT_SECRET == 'sandbox_secret'


def test_qbo_client_uses_production_credentials():
    """Test that production environment uses production credentials."""
    with patch.dict('os.environ', {
        'QBO_ENV': 'production',
        'QBO_CLIENT_ID': 'prod_client_id',
        'QBO_CLIENT_SECRET': 'prod_secret'
    }):
        from importlib import reload
        import app.integrations.qbo.client as client_module
        reload(client_module)
        
        assert client_module.QBO_CLIENT_ID == 'prod_client_id'
        assert client_module.QBO_CLIENT_SECRET == 'prod_secret'


@pytest.mark.asyncio
async def test_real_mode_calls_qbo_api(qbo_service, je_payload, db_session):
    """Test that real mode (not demo) attempts to call QBO API."""
    with patch('app.services.qbo.DEMO_MODE', False):
        # Mock token fetch
        with patch.object(qbo_service, 'get_fresh_token', return_value=("token", "realm")):
            # Mock QBO API call
            with patch.object(qbo_service.client, 'post_journal_entry') as mock_post:
                mock_post.return_value = {
                    "qbo_doc_id": "123",
                    "sync_token": "1"
                }
                
                result = await qbo_service.post_idempotent_je(
                    tenant_id="test-tenant",
                    payload=je_payload
                )
                
                # Verify QBO API was called
                mock_post.assert_called_once()
                assert result["qbo_doc_id"] == "123"
                assert "posted_mock" not in result


@pytest.mark.asyncio
async def test_demo_mode_does_not_call_qbo_api(qbo_service, je_payload):
    """Test that demo mode never calls real QBO API."""
    with patch('app.services.qbo.DEMO_MODE', True):
        # Mock QBO API call (should NOT be called)
        with patch.object(qbo_service.client, 'post_journal_entry') as mock_post:
            result = await qbo_service.post_idempotent_je(
                tenant_id="test-tenant",
                payload=je_payload
            )
            
            # Verify QBO API was NOT called
            mock_post.assert_not_called()
            assert result["posted_mock"] is True


@pytest.mark.integration
def test_qbo_build_journal_entry_payload():
    """Test that QBO client builds correct payload format."""
    client = QBOClient()
    
    payload = client.build_journal_entry_payload(
        txn_date="2025-10-27",
        lines=[
            {"account": "5000", "debit": 100, "credit": 0},
            {"account": "1000", "debit": 0, "credit": 100}
        ],
        ref_number="JE-001",
        private_note="Test"
    )
    
    assert payload["TxnDate"] == "2025-10-27"
    assert payload["DocNumber"] == "JE-001"
    assert payload["PrivateNote"] == "Test"
    assert len(payload["Line"]) == 2
    
    # Check line format
    line1 = payload["Line"][0]
    assert line1["JournalEntryLineDetail"]["AccountRef"]["value"] == "5000"
    assert line1["JournalEntryLineDetail"]["PostingType"] == "Debit"
    assert line1["Amount"] == 100

