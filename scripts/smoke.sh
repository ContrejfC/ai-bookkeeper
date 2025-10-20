#!/usr/bin/env bash
set -euo pipefail
: "${API_URL:?}"  # export API_URL or set from tmp/API_URL.txt
curl -fsSL "$API_URL/healthz" | grep -q '"status":"ok"' && echo "API health OK"
if [[ -n "${WEB_URL:-}" ]]; then
  curl -fsSI "$WEB_URL" | grep -E "200|301|302" >/dev/null && echo "WEB reachable"
  curl -fsS -X OPTIONS "$API_URL/healthz" -H "Origin: $WEB_URL" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: Content-Type" >/dev/null && echo "CORS preflight OK"
fi