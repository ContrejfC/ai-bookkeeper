#!/usr/bin/env bash
set -euo pipefail
: "${API_URL:?Set API_URL}"
: "${WEB_URL:?Set WEB_URL}"

curl -fsSL "$API_URL/healthz" | grep -q '"status":"ok"'
curl -fsSI "$WEB_URL" | grep -q "200"
curl -fsS -X OPTIONS "$API_URL/healthz" \
  -H "Origin: $WEB_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" >/dev/null
echo "smoke ok"

