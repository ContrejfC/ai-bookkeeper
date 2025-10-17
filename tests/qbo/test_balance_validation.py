"""
Tests for journal entry balance validation.
"""

import pytest


def test_balanced_entry_passes():
    """Test that balanced journal entry passes validation."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    lines = [
        {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
        {"amount": 150.00, "postingType": "Credit", "accountRef": {"value": "7"}}
    ]
    
    is_valid, error = service.validate_balance(lines)
    
    assert is_valid is True
    assert error is None


def test_unbalanced_entry_fails():
    """Test that unbalanced journal entry fails validation."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    lines = [
        {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
        {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "7"}}
    ]
    
    is_valid, error = service.validate_balance(lines)
    
    assert is_valid is False
    assert "must equal" in error.lower()
    assert "150" in error
    assert "100" in error


def test_multiple_lines_balanced():
    """Test validation with multiple debit and credit lines."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    lines = [
        {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "46"}},
        {"amount": 50.00, "postingType": "Debit", "accountRef": {"value": "47"}},
        {"amount": 75.00, "postingType": "Credit", "accountRef": {"value": "7"}},
        {"amount": 75.00, "postingType": "Credit", "accountRef": {"value": "8"}}
    ]
    
    is_valid, error = service.validate_balance(lines)
    
    assert is_valid is True  # 150 debit == 150 credit


def test_floating_point_tolerance():
    """Test that small floating point differences are tolerated."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    lines = [
        {"amount": 150.001, "postingType": "Debit", "accountRef": {"value": "46"}},
        {"amount": 150.000, "postingType": "Credit", "accountRef": {"value": "7"}}
    ]
    
    is_valid, error = service.validate_balance(lines)
    
    # Should pass - difference is < 0.01
    assert is_valid is True


def test_significant_imbalance_fails():
    """Test that significant imbalance fails validation."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    lines = [
        {"amount": 150.50, "postingType": "Debit", "accountRef": {"value": "46"}},
        {"amount": 149.00, "postingType": "Credit", "accountRef": {"value": "7"}}
    ]
    
    is_valid, error = service.validate_balance(lines)
    
    assert is_valid is False
    assert "150.50" in error and "149.00" in error


@pytest.mark.asyncio
async def test_unbalanced_je_raises_value_error():
    """Test that posting unbalanced JE raises ValueError."""
    from app.services.qbo import QBOService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db.models import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    service = QBOService(db)
    
    unbalanced_payload = {
        "txnDate": "2025-10-16",
        "lines": [
            {"amount": 150.00, "postingType": "Debit", "accountRef": {"value": "46"}},
            {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "7"}}
        ]
    }
    
    with pytest.raises(ValueError) as exc_info:
        await service.post_idempotent_je("test_tenant", unbalanced_payload)
    
    assert "UNBALANCED_JE" in str(exc_info.value)

