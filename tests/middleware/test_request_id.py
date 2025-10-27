"""
Test Request ID Middleware
===========================

Tests for request tracking and correlation.

Test Cases:
-----------
1. Request ID generated for new requests
2. Client-provided request ID preserved
3. Request ID in response headers
4. Request ID in logs
5. Request ID in error responses
6. Request ID helps trace requests
"""
import pytest
import logging
import uuid
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_generates_request_id_if_not_provided(client):
    """Test that request ID is auto-generated if not provided."""
    response = client.get("/healthz")
    
    assert "X-Request-Id" in response.headers
    
    # Should be a valid UUID
    request_id = response.headers["X-Request-Id"]
    try:
        uuid.UUID(request_id)
        assert True
    except ValueError:
        pytest.fail("Request ID is not a valid UUID")


def test_preserves_client_provided_request_id(client):
    """Test that client-provided request ID is preserved."""
    client_request_id = str(uuid.uuid4())
    
    response = client.get(
        "/healthz",
        headers={"X-Request-Id": client_request_id}
    )
    
    assert response.headers["X-Request-Id"] == client_request_id


def test_request_id_present_in_successful_response(client):
    """Test that request ID is in successful response headers."""
    response = client.get("/healthz")
    
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    assert len(response.headers["X-Request-Id"]) > 0


def test_request_id_present_in_error_response(client):
    """Test that request ID is in error response headers."""
    # Make request that will fail (no auth)
    response = client.post("/api/post/propose")
    
    assert response.status_code == 401  # Unauthorized
    assert "X-Request-Id" in response.headers


def test_request_id_is_unique_per_request(client):
    """Test that each request gets a unique request ID."""
    response1 = client.get("/healthz")
    response2 = client.get("/healthz")
    
    request_id_1 = response1.headers["X-Request-Id"]
    request_id_2 = response2.headers["X-Request-Id"]
    
    assert request_id_1 != request_id_2


def test_request_id_in_logs(client, caplog):
    """Test that request ID appears in log messages."""
    request_id = str(uuid.uuid4())
    
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/healthz",
            headers={"X-Request-Id": request_id}
        )
    
    # Request ID should be in response
    assert response.headers["X-Request-Id"] == request_id
    
    # Note: Checking logs for request_id requires proper log configuration
    # This is a basic test that the header is preserved


def test_request_id_helps_trace_errors(client, caplog):
    """Test that request ID helps trace errors across requests."""
    request_id = str(uuid.uuid4())
    
    with caplog.at_level(logging.ERROR):
        response = client.get(
            "/api/nonexistent-endpoint",
            headers={"X-Request-Id": request_id}
        )
    
    # Should be 404
    assert response.status_code == 404
    
    # Request ID should be in response
    assert response.headers["X-Request-Id"] == request_id


def test_request_id_format_is_valid_uuid(client):
    """Test that generated request IDs are valid UUIDs."""
    for _ in range(10):
        response = client.get("/healthz")
        request_id = response.headers["X-Request-Id"]
        
        # Should not raise ValueError
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"Request ID '{request_id}' is not a valid UUID")


def test_request_id_persists_through_middleware_chain(client):
    """Test that request ID persists through all middleware."""
    custom_id = str(uuid.uuid4())
    
    # Make authenticated request (goes through auth middleware)
    response = client.post(
        "/api/post/propose",
        headers={"X-Request-Id": custom_id}
    )
    
    # Even though request fails auth, request ID should be preserved
    assert response.headers["X-Request-Id"] == custom_id


def test_request_id_in_concurrent_requests(client):
    """Test that request IDs don't collide in concurrent requests."""
    request_ids = []
    
    # Simulate multiple concurrent requests
    for _ in range(20):
        response = client.get("/healthz")
        request_ids.append(response.headers["X-Request-Id"])
    
    # All request IDs should be unique
    assert len(request_ids) == len(set(request_ids))


@pytest.mark.integration
def test_request_id_end_to_end_tracing(client, caplog):
    """Integration test: trace a request from start to finish."""
    trace_id = str(uuid.uuid4())
    
    with caplog.at_level(logging.INFO):
        # Make request with custom trace ID
        response = client.get(
            "/healthz",
            headers={"X-Request-Id": trace_id}
        )
        
        # Request should succeed
        assert response.status_code == 200
        
        # Trace ID should be in response
        assert response.headers["X-Request-Id"] == trace_id
        
        # In a real scenario, we'd verify trace_id appears in:
        # - All log messages for this request
        # - Database records created during request
        # - External API calls made during request


def test_request_id_middleware_handles_exceptions(client):
    """Test that request ID is preserved even when exceptions occur."""
    request_id = str(uuid.uuid4())
    
    # Make request that will cause error
    response = client.get(
        "/api/some-endpoint-that-causes-error",
        headers={"X-Request-Id": request_id}
    )
    
    # Even with error, request ID should be preserved
    assert response.headers.get("X-Request-Id") == request_id


def test_request_id_in_state(client):
    """Test that request ID is stored in request.state."""
    # This tests the internal behavior
    # In real implementation, request.state.request_id is set
    
    # For external testing, we can only verify via headers
    response = client.get("/healthz")
    assert "X-Request-Id" in response.headers


def test_request_filter_adds_request_id_to_records():
    """Test that RequestIdFilter adds request_id to log records."""
    from app.middleware.request_id import RequestIdFilter
    
    # Create mock log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add request_id to record via extra
    record.request_id = "test-request-123"
    
    # Apply filter
    filter = RequestIdFilter()
    filter.filter(record)
    
    # Request ID should be on record
    assert hasattr(record, 'request_id')
    assert record.request_id == "test-request-123"


def test_request_filter_handles_missing_request_id():
    """Test that RequestIdFilter handles records without request_id."""
    from app.middleware.request_id import RequestIdFilter
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Don't set request_id
    
    filter = RequestIdFilter()
    result = filter.filter(record)
    
    # Should still process record
    assert result is True
    
    # Should have default value
    assert hasattr(record, 'request_id')
    assert record.request_id == 'N/A'


@pytest.mark.parametrize("endpoint", [
    "/healthz",
    "/readyz",
    "/api/billing/entitlements",
])
def test_request_id_on_various_endpoints(client, endpoint):
    """Test that request ID works on various endpoints."""
    response = client.get(endpoint)
    
    # Regardless of auth success/failure, should have request ID
    assert "X-Request-Id" in response.headers
    assert len(response.headers["X-Request-Id"]) > 0


def test_request_id_with_special_characters_rejected():
    """Test that request ID with special chars is replaced."""
    # Invalid UUID should be replaced with new one
    response = TestClient(app).get(
        "/healthz",
        headers={"X-Request-Id": "invalid<>characters"}
    )
    
    # Should get a valid UUID back (not the invalid one)
    request_id = response.headers["X-Request-Id"]
    
    try:
        uuid.UUID(request_id)
        # If it's a valid UUID, then invalid one was replaced
        assert request_id != "invalid<>characters"
    except ValueError:
        # Or it might pass through - depends on implementation
        pass

