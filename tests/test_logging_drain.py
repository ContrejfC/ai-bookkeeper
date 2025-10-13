"""
Tests for Log Drain functionality (SOC 2 Min Controls).

Tests:
- Log drain handler batches logs
- Retry logic with exponential backoff
- Graceful degradation to stdout on failure
- Dry-run behavior when drain URL not configured
"""
import logging
import time
from unittest.mock import Mock, patch, MagicMock

import pytest

from app.ops.logging import LogDrainHandler, PiiRedactingFormatter, configure_logging


def test_log_drain_handler_batching():
    """Test log drain batches logs before sending."""
    drain_handler = LogDrainHandler(
        drain_url="https://logs.example.com/ingest",
        batch_size=5,
        flush_interval=10.0  # Long interval to test batch trigger
    )
    drain_handler.setFormatter(PiiRedactingFormatter())
    
    # Add logs to buffer (less than batch size)
    for i in range(3):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Log message {i}",
            args=(),
            exc_info=None
        )
        drain_handler.emit(record)
    
    # Buffer should have 3 logs
    assert len(drain_handler.buffer) == 3
    
    drain_handler.close()


@patch('app.ops.logging.requests.post')
def test_log_drain_sends_on_batch_full(mock_post):
    """Test log drain sends when batch is full."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    drain_handler = LogDrainHandler(
        drain_url="https://logs.example.com/ingest",
        api_key="test-key-123",
        batch_size=3,  # Small batch for testing
        flush_interval=10.0
    )
    drain_handler.setFormatter(PiiRedactingFormatter())
    
    # Add exactly batch_size logs
    for i in range(3):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Log message {i}",
            args=(),
            exc_info=None
        )
        drain_handler.emit(record)
    
    # Give a moment for flush
    time.sleep(0.1)
    
    # Should have sent logs
    assert mock_post.called
    
    # Verify request
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://logs.example.com/ingest"
    assert "Authorization" in call_args[1]["headers"]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-key-123"
    
    # Buffer should be empty after flush
    assert len(drain_handler.buffer) == 0
    
    drain_handler.close()


@patch('app.ops.logging.requests.post')
def test_log_drain_retry_on_failure(mock_post):
    """Test log drain retries on failure."""
    # First two calls fail, third succeeds
    mock_post.side_effect = [
        Exception("Connection error"),
        Exception("Connection error"),
        Mock(status_code=200)
    ]
    
    drain_handler = LogDrainHandler(
        drain_url="https://logs.example.com/ingest",
        batch_size=1,
        flush_interval=10.0
    )
    drain_handler.setFormatter(PiiRedactingFormatter())
    
    # Add one log to trigger immediate flush
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    drain_handler.emit(record)
    
    time.sleep(0.5)  # Wait for retries
    
    # Should have retried 3 times
    assert mock_post.call_count == 3
    
    drain_handler.close()


@patch('app.ops.logging.requests.post')
@patch('sys.stderr')
def test_log_drain_degrades_to_stderr(mock_stderr, mock_post):
    """Test log drain degrades gracefully to stderr on persistent failure."""
    # All attempts fail
    mock_post.side_effect = Exception("Network unreachable")
    
    drain_handler = LogDrainHandler(
        drain_url="https://logs.example.com/ingest",
        batch_size=1,
        flush_interval=10.0
    )
    drain_handler.setFormatter(PiiRedactingFormatter())
    
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Critical error message",
        args=(),
        exc_info=None
    )
    
    with patch('builtins.print') as mock_print:
        drain_handler.emit(record)
        time.sleep(0.5)  # Wait for retries and fallback
        
        # Should have attempted 3 times
        assert mock_post.call_count == 3
        
        # Should have printed to stderr (degraded mode)
        assert mock_print.called
    
    drain_handler.close()


def test_configure_logging_without_drain(caplog):
    """Test logging configuration works without drain URL."""
    import os
    
    # Ensure no drain URL
    old_url = os.environ.get("LOG_DRAIN_URL")
    if old_url:
        del os.environ["LOG_DRAIN_URL"]
    
    try:
        logger = configure_logging()
        
        # Should configure without error
        assert logger is not None
        
        # Should have console handler only
        handlers = logger.handlers
        assert len(handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    
    finally:
        # Restore
        if old_url:
            os.environ["LOG_DRAIN_URL"] = old_url


@patch('app.ops.logging.LogDrainHandler')
def test_configure_logging_with_drain(mock_drain_handler):
    """Test logging configuration enables drain when URL provided."""
    import os
    
    # Set drain URL
    old_url = os.environ.get("LOG_DRAIN_URL")
    old_key = os.environ.get("LOG_DRAIN_API_KEY")
    os.environ["LOG_DRAIN_URL"] = "https://logs.example.com/ingest"
    os.environ["LOG_DRAIN_API_KEY"] = "test-key"
    
    try:
        logger = configure_logging()
        
        # Should have attempted to create drain handler
        assert mock_drain_handler.called
        
        # Verify drain handler was called with correct params
        call_args = mock_drain_handler.call_args
        assert call_args[0][0] == "https://logs.example.com/ingest"
        assert call_args[0][1] == "test-key"
    
    finally:
        # Restore
        if old_url:
            os.environ["LOG_DRAIN_URL"] = old_url
        else:
            del os.environ["LOG_DRAIN_URL"]
        
        if old_key:
            os.environ["LOG_DRAIN_API_KEY"] = old_key
        elif "LOG_DRAIN_API_KEY" in os.environ:
            del os.environ["LOG_DRAIN_API_KEY"]


@patch('app.ops.logging.requests.post')
def test_drain_sends_json_lines_format(mock_post):
    """Test drain sends logs in JSON-lines format (newline-delimited)."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    drain_handler = LogDrainHandler(
        drain_url="https://logs.example.com/ingest",
        batch_size=2,
        flush_interval=10.0
    )
    drain_handler.setFormatter(PiiRedactingFormatter())
    
    # Add two logs
    for i in range(2):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"Message {i}",
            args=(),
            exc_info=None
        )
        drain_handler.emit(record)
    
    time.sleep(0.1)
    
    # Verify JSON-lines format (newline-separated)
    assert mock_post.called
    sent_data = mock_post.call_args[1]["data"]
    
    lines = sent_data.split("\n")
    assert len(lines) == 2  # Two log entries
    
    # Each line should be valid JSON
    import json
    for line in lines:
        parsed = json.loads(line)
        assert "timestamp" in parsed
        assert "message" in parsed
    
    drain_handler.close()


def test_drain_handler_flush_on_close():
    """Test drain handler flushes remaining logs on close."""
    with patch('app.ops.logging.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        drain_handler = LogDrainHandler(
            drain_url="https://logs.example.com/ingest",
            batch_size=100,  # Large batch so logs stay buffered
            flush_interval=10.0
        )
        drain_handler.setFormatter(PiiRedactingFormatter())
        
        # Add logs (less than batch size)
        for i in range(5):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None
            )
            drain_handler.emit(record)
        
        # Logs should be buffered
        assert len(drain_handler.buffer) == 5
        
        # Close should flush
        drain_handler.close()
        
        time.sleep(0.1)
        
        # Should have sent logs
        assert mock_post.called

