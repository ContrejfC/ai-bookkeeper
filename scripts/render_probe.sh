#!/usr/bin/env bash
set -euo pipefail
: "${API_URL:?Set API_URL}"
: "${WEB_URL:?Set WEB_URL}"

echo "[probe] API /healthz"
curl -fsSL "$API_URL/healthz" | grep -q '"status":"ok"'

echo "[probe] WEB HEAD"
curl -fsSI "$WEB_URL" | grep -E "200|301|302" >/dev/null

echo "[probe] CORS preflight"
curl -fsS -X OPTIONS "$API_URL/healthz" \
  -H "Origin: $WEB_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" >/dev/null

echo "OK"