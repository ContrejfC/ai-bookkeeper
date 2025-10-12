#!/bin/bash
# Staging Verification Script
# Usage: ./scripts/verify_staging.sh https://ai-bookkeeper-app.onrender.com

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="${1:-}"

if [ -z "$BASE_URL" ]; then
    echo -e "${RED}❌ Error: BASE_URL is required${NC}"
    echo "Usage: $0 https://your-app.onrender.com"
    exit 1
fi

echo "🔍 Verifying staging at: $BASE_URL"
echo ""

# Test /healthz
echo "1️⃣  Testing /healthz..."
HEALTHZ_RESPONSE=$(curl -fsS "${BASE_URL}/healthz" 2>&1) || {
    echo -e "${RED}❌ /healthz failed to respond${NC}"
    exit 1
}

echo "$HEALTHZ_RESPONSE" | jq . > /dev/null 2>&1 || {
    echo -e "${RED}❌ /healthz did not return valid JSON${NC}"
    echo "$HEALTHZ_RESPONSE"
    exit 1
}

HEALTHZ_STATUS=$(echo "$HEALTHZ_RESPONSE" | jq -r '.status')
if [ "$HEALTHZ_STATUS" != "ok" ]; then
    echo -e "${YELLOW}⚠️  healthz status is: $HEALTHZ_STATUS (expected 'ok')${NC}"
else
    echo -e "${GREEN}✅ /healthz returned status: ok${NC}"
fi

# Extract and display key info
DB_STATUS=$(echo "$HEALTHZ_RESPONSE" | jq -r '.database_status // "unknown"')
DB_PING=$(echo "$HEALTHZ_RESPONSE" | jq -r '.db_ping_ms // "0"')
VERSION=$(echo "$HEALTHZ_RESPONSE" | jq -r '.version // "unknown"')
GIT_SHA=$(echo "$HEALTHZ_RESPONSE" | jq -r '.git_sha // "unknown"')

echo "   └─ Database: $DB_STATUS (${DB_PING}ms)"
echo "   └─ Version: $VERSION"
echo "   └─ Git SHA: $GIT_SHA"
echo ""

# Test /readyz
echo "2️⃣  Testing /readyz..."
READYZ_RESPONSE=$(curl -fsS "${BASE_URL}/readyz" 2>&1) || {
    echo -e "${RED}❌ /readyz failed to respond${NC}"
    exit 1
}

echo "$READYZ_RESPONSE" | jq . > /dev/null 2>&1 || {
    echo -e "${RED}❌ /readyz did not return valid JSON${NC}"
    echo "$READYZ_RESPONSE"
    exit 1
}

READYZ_STATUS=$(echo "$READYZ_RESPONSE" | jq -r '.status')
if [ "$READYZ_STATUS" != "ready" ] && [ "$READYZ_STATUS" != "ok" ]; then
    echo -e "${YELLOW}⚠️  readyz status is: $READYZ_STATUS${NC}"
else
    echo -e "${GREEN}✅ /readyz returned status: $READYZ_STATUS${NC}"
fi

# Extract migration info
ALEMBIC_VERSION=$(echo "$READYZ_RESPONSE" | jq -r '.checks.migrations.current // .alembic_version // .current_migration // "unknown"')
MIGRATION_STATUS=$(echo "$READYZ_RESPONSE" | jq -r '.checks.migrations.status // "unknown"')

echo "   └─ Alembic version: $ALEMBIC_VERSION"
echo "   └─ Migration status: $MIGRATION_STATUS"
echo ""

# Test root API
echo "3️⃣  Testing root API (/)..."
ROOT_RESPONSE=$(curl -fsS "${BASE_URL}/" 2>&1) || {
    echo -e "${YELLOW}⚠️  Root API did not respond (non-fatal)${NC}"
}

if echo "$ROOT_RESPONSE" | jq . > /dev/null 2>&1; then
    API_MESSAGE=$(echo "$ROOT_RESPONSE" | jq -r '.message // "unknown"')
    API_VERSION=$(echo "$ROOT_RESPONSE" | jq -r '.version // "unknown"')
    echo -e "${GREEN}✅ Root API responded${NC}"
    echo "   └─ Message: $API_MESSAGE"
    echo "   └─ Version: $API_VERSION"
else
    echo -e "${YELLOW}⚠️  Root API returned non-JSON (possibly HTML)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ All critical health checks passed!${NC}"
echo ""
echo "📊 Summary:"
echo "   • Healthz: $HEALTHZ_STATUS"
echo "   • Readyz: $READYZ_STATUS"
echo "   • Database: $DB_STATUS"
echo "   • Alembic: $ALEMBIC_VERSION"
echo ""
echo "🔗 Base URL: $BASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
