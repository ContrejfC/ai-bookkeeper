"""
Test fixtures for billing tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mock_stripe(monkeypatch):
    """Mock Stripe API calls."""
    class MockStripe:
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {
                        'url': 'https://checkout.stripe.com/test_session',
                        'id': 'cs_test_123'
                    })
        
        class billing_portal:
            class Session:
                @staticmethod
                def create(**kwargs):
                    return type('obj', (object,), {
                        'url': 'https://billing.stripe.com/test_portal'
                    })
        
        class Price:
            @staticmethod
            def retrieve(price_id):
                return {
                    'id': price_id,
                    'metadata': {
                        'plan': 'starter',
                        'tx_cap': '300',
                        'bulk_approve': 'false',
                        'included_companies': '1'
                    }
                }
        
        class Webhook:
            @staticmethod
            def construct_event(payload, sig_header, secret):
                import json
                return json.loads(payload)
        
        class error:
            class StripeError(Exception):
                pass
            
            class SignatureVerificationError(Exception):
                pass
    
    return MockStripe()

