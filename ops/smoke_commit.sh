#!/bin/bash
# Smoke test for /post/commit endpoint with idempotency
#
# Prerequisites:
# - Server running with QBO connected
# - $TOKEN environment variable set
#
# Usage:
#   export TOKEN=your_jwt_token
#   ./ops/smoke_commit.sh

set -e

BASE_URL=${BASE_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}

if [ -z "$TOKEN" ]; then
    echo "❌ ERROR: TOKEN environment variable not set"
    echo "Usage: export TOKEN=your_jwt_token && ./ops/smoke_commit.sh"
    exit 1
fi

echo "=== Smoke Test: /post/commit with Idempotency ==="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Post two approvals (first time)
echo "Test 1: Posting two journal entries..."
RESPONSE1=$(curl -s -X POST "$BASE_URL/api/post/commit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approvals": [
      {
        "txn_id": "smoke_test_1",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "SMOKE-001",
          "privateNote": "Smoke test 1",
          "lines": [
            {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "1"}},
            {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "30"}}
          ]
        }
      },
      {
        "txn_id": "smoke_test_2",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "SMOKE-002",
          "privateNote": "Smoke test 2",
          "lines": [
            {"amount": 50.00, "postingType": "Debit", "accountRef": {"value": "46"}},
            {"amount": 50.00, "postingType": "Credit", "accountRef": {"value": "33"}}
          ]
        }
      }
    ]
  }')

echo "$RESPONSE1" | python3 -m json.tool
echo ""

# Test 2: Post same entries again (should be idempotent)
echo "Test 2: Posting same entries again (idempotency check)..."
RESPONSE2=$(curl -s -X POST "$BASE_URL/api/post/commit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approvals": [
      {
        "txn_id": "smoke_test_1",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "SMOKE-001",
          "privateNote": "Smoke test 1",
          "lines": [
            {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "1"}},
            {"amount": 100.00, "postingType": "Credit", "accountRef": {"value": "30"}}
          ]
        }
      },
      {
        "txn_id": "smoke_test_2",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "SMOKE-002",
          "privateNote": "Smoke test 2",
          "lines": [
            {"amount": 50.00, "postingType": "Debit", "accountRef": {"value": "46"}},
            {"amount": 50.00, "postingType": "Credit", "accountRef": {"value": "33"}}
          ]
        }
      }
    ]
  }')

echo "$RESPONSE2" | python3 -m json.tool
echo ""

# Test 3: Post unbalanced entry
echo "Test 3: Posting unbalanced entry (should return item error)..."
RESPONSE3=$(curl -s -X POST "$BASE_URL/api/post/commit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approvals": [
      {
        "txn_id": "smoke_test_unbalanced",
        "je": {
          "txnDate": "2025-10-17",
          "refNumber": "SMOKE-ERR",
          "lines": [
            {"amount": 100.00, "postingType": "Debit", "accountRef": {"value": "1"}},
            {"amount": 50.00, "postingType": "Credit", "accountRef": {"value": "30"}}
          ]
        }
      }
    ]
  }')

echo "$RESPONSE3" | python3 -m json.tool
echo ""

echo "=== Smoke Test Complete ==="
echo ""
echo "Expected Results:"
echo "- Test 1: Both entries posted (status=posted, idempotent=false)"
echo "- Test 2: Both entries idempotent (status=posted, idempotent=true, same qbo_doc_id)"
echo "- Test 3: Error returned (status=error, code=UNBALANCED_JE)"

