#!/usr/bin/env bash
#
# Smoke Tests for GCP Deployment
# ===============================
#
# Quick validation tests for Google Cloud Run deployment

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get URLs from deployment
if [[ -f "tmp/API_URL.txt" ]]; then
    API_URL=$(cat tmp/API_URL.txt)
else
    echo -e "${RED}❌ API URL not found. Please deploy first.${NC}"
    exit 1
fi

if [[ -f "tmp/WEB_URL.txt" ]]; then
    WEB_URL=$(cat tmp/WEB_URL.txt)
else
    echo -e "${YELLOW}⚠️  Web URL not found (optional)${NC}"
    WEB_URL=""
fi

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   AI Bookkeeper - GCP Smoke Tests                        ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo "Testing API: $API_URL"
[[ -n "$WEB_URL" ]] && echo "Testing Web: $WEB_URL"
echo ""

PASS=0
FAIL=0

# Test function
run_test() {
    local test_name=$1
    local command=$2
    local expected=$3
    
    echo -n "Testing: $test_name ... "
    
    if result=$(eval "$command" 2>&1); then
        if echo "$result" | grep -q "$expected"; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASS++))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}"
            echo "  Expected: $expected"
            echo "  Got: $result"
            ((FAIL++))
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL (command error)${NC}"
        echo "  Error: $result"
        ((FAIL++))
        return 1
    fi
}

echo -e "${BLUE}Running Smoke Tests...${NC}"
echo ""

# Test 1: Health endpoint
run_test "Health Endpoint" \
    "curl -s $API_URL/healthz" \
    "healthy"

# Test 2: Readiness endpoint
run_test "Readiness Endpoint" \
    "curl -s $API_URL/readyz" \
    "ready"

# Test 3: API responds (any endpoint)
run_test "API Response" \
    "curl -s -o /dev/null -w '%{http_code}' $API_URL/healthz" \
    "200"

# Test 4: CORS headers present
run_test "CORS Headers" \
    "curl -s -I $API_URL/healthz | grep -i 'access-control'" \
    "access-control"

# Test 5: Request ID header
run_test "Request ID Header" \
    "curl -s -I $API_URL/healthz | grep -i 'x-request-id'" \
    "X-Request-Id"

# Test 6: OpenAPI docs available
run_test "OpenAPI Docs" \
    "curl -s $API_URL/docs | head -1" \
    "html"

# Test 7: Frontend accessible (if deployed)
if [[ -n "$WEB_URL" ]]; then
    run_test "Frontend Home Page" \
        "curl -s -o /dev/null -w '%{http_code}' $WEB_URL" \
        "200"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Summary:${NC}"
echo -e "  ${GREEN}Passed: $PASS${NC}"
echo -e "  ${RED}Failed: $FAIL${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    echo ""
    echo "🎉 Your MVP is live and healthy on Google Cloud!"
    echo ""
    echo "Next steps:"
    echo "  1. Test onboarding: $WEB_URL/welcome"
    echo "  2. Run full test suite locally"
    echo "  3. Configure production environment variables"
    echo "  4. Set up monitoring alerts"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please investigate.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check logs: gcloud run logs read ai-bookkeeper-api-mvp"
    echo "  - Verify environment variables"
    echo "  - Check service status: gcloud run services list"
    echo ""
    exit 1
fi

