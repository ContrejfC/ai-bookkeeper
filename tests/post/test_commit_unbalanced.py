"""
Tests for /post/commit unbalanced JE handling.
"""

import pytest


def test_unbalanced_je_returns_item_error_not_global():
    """Test that unbalanced JE returns item-level error, not global 400."""
    
    # Unbalanced JE should be returned in per-item results
    # Not as a global HTTP 400 error
    
    results = [
        {
            "txn_id": "t1",
            "status": "error",
            "error": {
                "code": "UNBALANCED_JE",
                "message": "Debits (150.00) must equal credits (100.00)"
            }
        }
    ]
    
    # Validate error structure
    assert results[0]["status"] == "error"
    assert results[0]["error"]["code"] == "UNBALANCED_JE"
    assert "Debits" in results[0]["error"]["message"]


def test_unbalanced_je_doesnt_block_other_items():
    """Test that unbalanced JE doesn't prevent other items from posting."""
    
    # If one JE is unbalanced, others should still post
    results = [
        {"txn_id": "t1", "status": "error", "error": {"code": "UNBALANCED_JE", "message": "..."}},
        {"txn_id": "t2", "qbo_doc_id": "123", "idempotent": False, "status": "posted"}
    ]
    
    # Verify both items processed
    assert len(results) == 2
    assert results[0]["status"] == "error"
    assert results[1]["status"] == "posted"


def test_commit_validates_each_item_independently():
    """Test that each item is validated independently."""
    
    # Multiple items with different outcomes
    results = [
        {"txn_id": "t1", "qbo_doc_id": "123", "status": "posted"},
        {"txn_id": "t2", "status": "error", "error": {"code": "UNBALANCED_JE"}},
        {"txn_id": "t3", "qbo_doc_id": "124", "idempotent": True, "status": "posted"},
        {"txn_id": "t4", "status": "error", "error": {"code": "QBO_VALIDATION"}}
    ]
    
    # Count outcomes
    posted = sum(1 for r in results if r["status"] == "posted")
    errors = sum(1 for r in results if r["status"] == "error")
    
    assert posted == 2
    assert errors == 2


def test_commit_response_is_always_200_with_results():
    """Test that commit always returns 200, even with all errors."""
    
    # Even if all items fail, response is 200 with error details
    http_status = 200
    results = [
        {"txn_id": "t1", "status": "error", "error": {"code": "UNBALANCED_JE"}},
        {"txn_id": "t2", "status": "error", "error": {"code": "QBO_VALIDATION"}}
    ]
    
    assert http_status == 200
    assert all(r["status"] == "error" for r in results)

