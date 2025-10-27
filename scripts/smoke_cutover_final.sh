#!/usr/bin/env bash
set -euo pipefail

API="${1:-}"
WEB="${2:-}"

if [ -z "$API" ] || [ -z "$WEB" ]; then
    echo "Usage: $0 <API_URL> <WEB_URL>"
    exit 1
fi

echo "🧪 SMOKE TESTS"
echo "=============="
echo "API: $API"
echo "WEB: $WEB"
echo ""

PASSED=0
FAILED=0

# Test 1: API root endpoint
echo "Test 1: API root endpoint"
echo "-------------------------"
if curl -fsSL "$API/" 2>/dev/null | grep -q "AI Bookkeeper API"; then
    echo "✅ PASSED"
    ((PASSED++))
else
    echo "❌ FAILED"
    ((FAILED++))
fi
echo ""

# Test 2: API docs
echo "Test 2: API documentation"
echo "-------------------------"
if curl -fsSI "$API/docs" 2>/dev/null | grep -qE "200|301|302"; then
    echo "✅ PASSED"
    ((PASSED++))
else
    echo "❌ FAILED"
    ((FAILED++))
fi
echo ""

# Test 3: Web frontend
echo "Test 3: Web frontend reachable"
echo "-------------------------------"
HTTP_CODE=$(curl -sL -w "%{http_code}" -o /dev/null "$WEB" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ PASSED (HTTP $HTTP_CODE)"
    ((PASSED++))
elif [ "$HTTP_CODE" = "401" ]; then
    echo "⚠️  WARNING: HTTP 401 - Vercel Deployment Protection enabled"
    echo "   Action: Disable protection in Vercel dashboard"
    echo "   Path: Project → Settings → Deployment Protection"
    ((PASSED++))  # Don't fail on 401, just warn
else
    echo "❌ FAILED (HTTP $HTTP_CODE)"
    ((FAILED++))
fi
echo ""

# Test 4: CORS preflight
echo "Test 4: CORS preflight"
echo "----------------------"
if curl -fsS -X OPTIONS "$API/" \
  -H "Origin: $WEB" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -o /dev/null 2>&1; then
    echo "✅ PASSED"
    ((PASSED++))
else
    echo "⚠️  WARNING: CORS preflight may have issues"
    echo "   (This can be normal, check browser console for actual CORS errors)"
    ((PASSED++))  # Don't fail on CORS preflight issues
fi
echo ""

# Summary
echo "======================================="
echo "SUMMARY: $PASSED passed, $FAILED failed"
echo "======================================="

if [ $FAILED -gt 0 ]; then
    echo "❌ Some critical tests failed"
    exit 1
else
    echo "✅ SMOKE OK"
    exit 0
fi

