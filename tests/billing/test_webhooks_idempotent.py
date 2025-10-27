"""
Test Stripe Webhook Idempotency
================================

Tests to ensure webhook events are processed idempotently.

Test Cases:
-----------
1. Webhook event processed successfully
2. Duplicate event returns success without processing
3. Signature verification required
4. Invalid signature rejected
5. checkout.session.completed creates subscription
6. customer.subscription.updated modifies status
7. customer.subscription.deleted marks cancelled
8. invoice.paid updates billing
"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.api.main import app
from app.db.models import BillingEventDB, BillingSubscriptionDB, TenantDB


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_stripe_event():
    """Mock Stripe event payload."""
    return {
        "id": "evt_test_123",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test_123",
                "customer": "cus_test_123",
                "status": "active",
                "items": {
                    "data": [{
                        "price": {
                            "id": "price_professional_monthly",
                            "lookup_key": "professional"
                        }
                    }]
                },
                "metadata": {
                    "tenant_id": "test-tenant-001"
                }
            }
        }
    }


@pytest.fixture
def stripe_signature():
    """Generate valid Stripe signature."""
    return "t=1234567890,v1=test_signature_here"


def test_webhook_processes_new_event(client, db_session, mock_stripe_event, stripe_signature):
    """Test that new webhook event is processed successfully."""
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = mock_stripe_event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=mock_stripe_event,
            headers={"Stripe-Signature": stripe_signature}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify event was logged
        event_log = db_session.query(BillingEventDB).filter_by(
            stripe_event_id="evt_test_123"
        ).first()
        
        assert event_log is not None
        assert event_log.type == "customer.subscription.created"
        assert event_log.processed is True


def test_webhook_idempotent_duplicate_event(client, db_session, mock_stripe_event, stripe_signature):
    """Test that duplicate webhook events are handled idempotently."""
    # Pre-create event log (simulate already processed)
    existing_event = BillingEventDB(
        type="customer.subscription.created",
        stripe_event_id="evt_test_123",
        payload_json=mock_stripe_event["data"],
        processed=True
    )
    db_session.add(existing_event)
    db_session.commit()
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = mock_stripe_event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=mock_stripe_event,
            headers={"Stripe-Signature": stripe_signature}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "already processed" in data["message"]
        
        # Verify no duplicate event log created
        event_count = db_session.query(BillingEventDB).filter_by(
            stripe_event_id="evt_test_123"
        ).count()
        
        assert event_count == 1


def test_webhook_requires_signature(client, mock_stripe_event):
    """Test that webhook without signature is rejected."""
    response = client.post(
        "/api/billing/stripe_webhook",
        json=mock_stripe_event
    )
    
    # Should fail without signature header
    assert response.status_code in [400, 401]


def test_webhook_rejects_invalid_signature(client, mock_stripe_event):
    """Test that webhook with invalid signature is rejected."""
    with patch('stripe.Webhook.construct_event') as mock_construct:
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=mock_stripe_event,
            headers={"Stripe-Signature": "invalid_signature"}
        )
        
        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()


def test_webhook_checkout_completed_creates_subscription(client, db_session):
    """Test that checkout.session.completed creates subscription."""
    event = {
        "id": "evt_checkout_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_new_123",
                "subscription": "sub_new_123",
                "client_reference_id": "tenant-new-001",
                "metadata": {
                    "tenant_id": "tenant-new-001"
                }
            }
        }
    }
    
    # Create tenant
    tenant = TenantDB(
        tenant_id="tenant-new-001",
        name="New Company"
    )
    db_session.add(tenant)
    db_session.commit()
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=event,
            headers={"Stripe-Signature": "sig"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was created
        subscription = db_session.query(BillingSubscriptionDB).filter_by(
            tenant_id="tenant-new-001"
        ).first()
        
        assert subscription is not None
        assert subscription.stripe_customer_id == "cus_new_123"
        assert subscription.stripe_subscription_id == "sub_new_123"


def test_webhook_subscription_updated_changes_status(client, db_session):
    """Test that customer.subscription.updated modifies subscription status."""
    # Create existing subscription
    subscription = BillingSubscriptionDB(
        tenant_id="test-tenant-002",
        plan_id="starter",
        status="active",
        stripe_customer_id="cus_test_456",
        stripe_subscription_id="sub_test_456"
    )
    db_session.add(subscription)
    db_session.commit()
    
    event = {
        "id": "evt_update_123",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_456",
                "customer": "cus_test_456",
                "status": "past_due",
                "items": {
                    "data": [{
                        "price": {
                            "lookup_key": "professional"
                        }
                    }]
                }
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=event,
            headers={"Stripe-Signature": "sig"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was updated
        db_session.refresh(subscription)
        assert subscription.status == "past_due"
        assert subscription.plan_id == "professional"


def test_webhook_subscription_deleted_marks_cancelled(client, db_session):
    """Test that customer.subscription.deleted marks subscription as cancelled."""
    # Create active subscription
    subscription = BillingSubscriptionDB(
        tenant_id="test-tenant-003",
        plan_id="starter",
        status="active",
        stripe_customer_id="cus_test_789",
        stripe_subscription_id="sub_test_789"
    )
    db_session.add(subscription)
    db_session.commit()
    
    event = {
        "id": "evt_delete_123",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_789",
                "customer": "cus_test_789",
                "status": "canceled"
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=event,
            headers={"Stripe-Signature": "sig"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was cancelled
        db_session.refresh(subscription)
        assert subscription.status == "cancelled"


def test_webhook_invoice_paid_logs_payment(client, db_session):
    """Test that invoice.paid event is processed and logged."""
    event = {
        "id": "evt_invoice_123",
        "type": "invoice.paid",
        "data": {
            "object": {
                "id": "in_test_123",
                "customer": "cus_test_999",
                "subscription": "sub_test_999",
                "amount_paid": 2900,
                "currency": "usd"
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=event,
            headers={"Stripe-Signature": "sig"}
        )
        
        assert response.status_code == 200
        
        # Verify event was logged
        event_log = db_session.query(BillingEventDB).filter_by(
            stripe_event_id="evt_invoice_123"
        ).first()
        
        assert event_log is not None
        assert event_log.processed is True


def test_webhook_handles_unknown_event_type(client, db_session):
    """Test that unknown event types are logged but don't error."""
    event = {
        "id": "evt_unknown_123",
        "type": "customer.unknown_event",
        "data": {
            "object": {}
        }
    }
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event
        
        response = client.post(
            "/api/billing/stripe_webhook",
            json=event,
            headers={"Stripe-Signature": "sig"}
        )
        
        assert response.status_code == 200
        
        # Verify event was still logged
        event_log = db_session.query(BillingEventDB).filter_by(
            stripe_event_id="evt_unknown_123"
        ).first()
        
        assert event_log is not None


@pytest.mark.integration
def test_webhook_race_condition_handling(client, db_session, mock_stripe_event):
    """Test concurrent webhook processing (race condition)."""
    # This tests that if two webhooks arrive simultaneously,
    # only one gets processed
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = mock_stripe_event
        
        # Send same event twice simultaneously (simulated)
        response1 = client.post(
            "/api/billing/stripe_webhook",
            json=mock_stripe_event,
            headers={"Stripe-Signature": "sig1"}
        )
        
        response2 = client.post(
            "/api/billing/stripe_webhook",
            json=mock_stripe_event,
            headers={"Stripe-Signature": "sig2"}
        )
        
        # Both should return success
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # But only one event log should exist
        event_count = db_session.query(BillingEventDB).filter_by(
            stripe_event_id="evt_test_123"
        ).count()
        
        assert event_count == 1

