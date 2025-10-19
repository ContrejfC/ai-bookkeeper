#!/usr/bin/env bash
set -euo pipefail

WEB_URL="${WEB_URL:-}"
API_URL="${API_URL:-}"

if [ -z "$WEB_URL" ] || [ -z "$API_URL" ]; then
  echo "❌ Set WEB_URL and API_URL env vars before running."
  echo "Example:"
  echo "  export API_URL=https://ai-bookkeeper-api.onrender.com"
  echo "  export WEB_URL=https://ai-bookkeeper-web.onrender.com"
  echo "  ./scripts/smoke.sh"
  exit 1
fi

echo "🔍 Running smoke tests..."
echo "  API: $API_URL"
echo "  WEB: $WEB_URL"
echo ""

# Test 1: API health check
echo "1️⃣  Checking API health..."
HEALTH_RESPONSE=$(curl -fsSL "$API_URL/healthz" || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"' || echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
  echo "   ✅ API health check passed"
else
  echo "   ❌ API health check failed: $HEALTH_RESPONSE"
  exit 1
fi

# Test 2: Web homepage
echo "2️⃣  Checking WEB homepage..."
HTTP_CODE=$(curl -fsSI "$WEB_URL" -o /dev/null -w "%{http_code}" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  echo "   ✅ WEB homepage returned 200"
else
  echo "   ❌ WEB homepage returned $HTTP_CODE"
  exit 1
fi

# Test 3: CORS preflight
echo "3️⃣  Checking CORS preflight..."
CORS_RESPONSE=$(curl -fsS -X OPTIONS "$API_URL/healthz" \
  -H "Origin: $WEB_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -w "%{http_code}" -o /dev/null || echo "000")

if [ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ]; then
  echo "   ✅ CORS preflight passed"
else
  echo "   ⚠️  CORS preflight returned $CORS_RESPONSE (may need ALLOWED_ORIGINS env var update)"
fi

echo ""
echo "✅ All smoke tests passed!"
echo ""
echo "📋 Next steps:"
echo "  1. Verify ALLOWED_ORIGINS on API includes: $WEB_URL"
echo "  2. Test full user flows in browser"
echo "  3. Check logs for any errors"

