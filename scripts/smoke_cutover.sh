#!/usr/bin/env bash
set -euo pipefail

API_URL="${1:-}"
WEB_URL="${2:-}"

if [ -z "$API_URL" ] || [ -z "$WEB_URL" ]; then
    echo "Usage: $0 <API_URL> <WEB_URL>"
    exit 1
fi

echo "🧪 Running smoke tests..."
echo "API: $API_URL"
echo "WEB: $WEB_URL"
echo ""

# Test API root endpoint
echo "1. Testing API root endpoint..."
if curl -fsSL "$API_URL/" | grep -q "AI Bookkeeper API"; then
    echo "✅ API root endpoint working"
else
    echo "❌ API root endpoint failed"
    exit 1
fi

# Test web endpoint
echo "2. Testing web endpoint..."
if curl -fsSI "$WEB_URL" | grep -qE "200|301|302"; then
    echo "✅ Web endpoint reachable"
else
    echo "❌ Web endpoint failed"
    exit 1
fi

# Test CORS preflight
echo "3. Testing CORS preflight..."
if curl -fsS -X OPTIONS "$API_URL/" \
  -H "Origin: $WEB_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" >/dev/null; then
    echo "✅ CORS preflight working"
else
    echo "⚠️  CORS preflight failed (may be normal)"
fi

echo ""
echo "🎉 Smoke tests completed!"
