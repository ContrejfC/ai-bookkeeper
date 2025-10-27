#!/bin/bash
# ============================================================================
# Background Jobs System - Quick Test Script
# ============================================================================
# 
# This script tests the background jobs API endpoints.
# 
# Usage:
#   chmod +x TEST_BACKGROUND_JOBS.sh
#   ./TEST_BACKGROUND_JOBS.sh
# 
# Prerequisites:
#   - Backend running on http://localhost:8000
#   - Valid authentication token (or modify script to use test mode)
# ============================================================================

set -e

BASE_URL="${API_URL:-http://localhost:8000}"
COMPANY_ID="${COMPANY_ID:-demo-company}"
TENANT_ID="${TENANT_ID:-demo-tenant}"

echo "🧪 Testing Background Jobs System"
echo "=================================="
echo ""
echo "Base URL: $BASE_URL"
echo "Company: $COMPANY_ID"
echo "Tenant: $TENANT_ID"
echo ""

# ============================================================================
# Test 1: Start Categorization Job
# ============================================================================
echo "📝 Test 1: Starting categorization job..."

RESPONSE=$(curl -s -X POST "$BASE_URL/api/jobs/categorize" \
  -H "Content-Type: application/json" \
  -d "{
    \"company_id\": \"$COMPANY_ID\",
    \"tenant_id\": \"$TENANT_ID\",
    \"limit\": 10
  }" || echo '{"error": "Request failed"}')

echo "Response: $RESPONSE"
echo ""

# Extract job_id
JOB_ID=$(echo "$RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4 || echo "")

if [ -z "$JOB_ID" ]; then
  echo "❌ Failed to get job_id from response"
  echo "   This might be because:"
  echo "   - Backend is not running"
  echo "   - Authentication is required"
  echo "   - Job queue is not available"
  echo ""
  exit 1
fi

echo "✅ Job created: $JOB_ID"
echo ""

# ============================================================================
# Test 2: Poll Job Status
# ============================================================================
echo "📊 Test 2: Polling job status..."
echo ""

for i in {1..10}; do
  echo "Poll #$i ($(date +%H:%M:%S)):"
  
  STATUS_RESPONSE=$(curl -s "$BASE_URL/api/jobs/$JOB_ID" || echo '{"error": "Request failed"}')
  
  # Extract fields
  STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
  PROGRESS=$(echo "$STATUS_RESPONSE" | grep -o '"progress":[0-9]*' | cut -d':' -f2 || echo "0")
  MESSAGE=$(echo "$STATUS_RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 || echo "")
  
  echo "  Status: $STATUS"
  echo "  Progress: $PROGRESS%"
  echo "  Message: $MESSAGE"
  echo ""
  
  # Stop if complete or failed
  if [ "$STATUS" = "complete" ] || [ "$STATUS" = "failed" ]; then
    echo "Job finished with status: $STATUS"
    echo ""
    echo "Full response:"
    echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
    echo ""
    break
  fi
  
  # Wait before next poll
  sleep 2
done

# ============================================================================
# Test 3: Get Company Jobs
# ============================================================================
echo "📋 Test 3: Getting company jobs..."

COMPANY_JOBS=$(curl -s "$BASE_URL/api/jobs/company/$COMPANY_ID?limit=10" || echo '{"error": "Request failed"}')

echo "Company jobs response:"
echo "$COMPANY_JOBS" | python3 -m json.tool 2>/dev/null || echo "$COMPANY_JOBS"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo "✅ Tests complete!"
echo ""
echo "What to do next:"
echo "  1. Check the frontend demo: http://localhost:10000/dashboard/background-jobs"
echo "  2. Review the guide: cat BACKGROUND_JOBS_GUIDE.md"
echo "  3. Check visual flow: cat BACKGROUND_JOBS_VISUAL_FLOW.md"
echo ""
echo "To test with authentication:"
echo "  1. Get your auth token from browser DevTools"
echo "  2. Add header: -H 'Cookie: session=YOUR_TOKEN'"
echo ""

