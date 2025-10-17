#!/usr/bin/env bash
# ops/pre_deploy_check.sh
# Pre-flight checks before deploying to Render (runs locally)

set -e

echo "🔍 PRE-DEPLOY VERIFICATION"
echo "=========================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_pass() {
  echo -e "${GREEN}✅ $1${NC}"
  PASS=$((PASS + 1))
}

check_fail() {
  echo -e "${RED}❌ $1${NC}"
  FAIL=$((FAIL + 1))
}

check_warn() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Check Dockerfile.api has no build-time side effects
echo "1. Checking Dockerfile.api..."
if grep -q "RUN.*alembic upgrade" Dockerfile.api 2>/dev/null; then
  check_fail "Dockerfile.api has build-time migrations (RUN alembic)"
elif grep -q "RUN.*pytest" Dockerfile.api 2>/dev/null; then
  check_fail "Dockerfile.api has build-time tests (RUN pytest)"
else
  check_pass "Dockerfile.api is clean (no build-time migrations/tests)"
fi

# 2. Check Dockerfile.web has standalone output
echo "2. Checking Dockerfile.web..."
if ! grep -q "output: 'standalone'" frontend/next.config.js 2>/dev/null; then
  check_fail "frontend/next.config.js missing output: 'standalone'"
else
  check_pass "Next.js configured for standalone output"
fi

# 3. Check $PORT binding in Dockerfiles
echo "3. Checking \$PORT binding..."
if ! grep -q '\${PORT' Dockerfile.api 2>/dev/null && ! grep -q '\$PORT' Dockerfile.api 2>/dev/null; then
  check_fail "Dockerfile.api does not bind to \$PORT"
else
  check_pass "Dockerfile.api binds to \$PORT"
fi

if ! grep -q '\${PORT' Dockerfile.web 2>/dev/null && ! grep -q '\$PORT' Dockerfile.web 2>/dev/null; then
  check_fail "Dockerfile.web does not bind to \$PORT"
else
  check_pass "Dockerfile.web binds to \$PORT"
fi

# 4. Check render-split.yaml exists and is valid
echo "4. Checking render-split.yaml..."
if [ ! -f "render-split.yaml" ]; then
  check_fail "render-split.yaml not found"
elif ! grep -q "ai-bookkeeper-api" render-split.yaml || ! grep -q "ai-bookkeeper-web" render-split.yaml; then
  check_fail "render-split.yaml missing required services"
else
  check_pass "render-split.yaml found and has required services"
fi

# 5. Check health check paths
echo "5. Checking health check paths..."
if ! grep -q 'healthCheckPath: /healthz' render-split.yaml; then
  check_warn "render-split.yaml may have incorrect health check paths (should be /healthz)"
else
  check_pass "Health check paths configured (/healthz)"
fi

# 6. Check that OpenAPI versioning files exist
echo "6. Checking OpenAPI versioning..."
if [ ! -f "docs/openapi-v1.0.json" ]; then
  check_warn "docs/openapi-v1.0.json not found (optional but recommended)"
elif [ ! -f "docs/openapi-latest.json" ]; then
  check_warn "docs/openapi-latest.json not found (optional but recommended)"
else
  check_pass "OpenAPI versioning files present"
fi

# 7. Check that smoke test script is executable
echo "7. Checking smoke test script..."
if [ ! -x "ops/smoke_live.sh" ]; then
  check_warn "ops/smoke_live.sh not executable (chmod +x ops/smoke_live.sh)"
else
  check_pass "ops/smoke_live.sh is executable"
fi

# 8. Check that db_migrate.sh exists and is executable
echo "8. Checking migration script..."
if [ ! -f "scripts/db_migrate.sh" ]; then
  check_fail "scripts/db_migrate.sh not found"
elif [ ! -x "scripts/db_migrate.sh" ]; then
  check_warn "scripts/db_migrate.sh not executable (chmod +x scripts/db_migrate.sh)"
else
  check_pass "scripts/db_migrate.sh is executable"
fi

# 9. Check that verification scripts exist
echo "9. Checking verification scripts..."
VERIFICATION_SCRIPTS=(
  "scripts/verify_prod_env.py"
  "scripts/check_qbo_env.py"
  "scripts/verify_stripe_webhook.py"
)

VERIFICATION_OK=0
for script in "${VERIFICATION_SCRIPTS[@]}"; do
  if [ ! -f "$script" ]; then
    check_warn "$script not found (optional but recommended)"
  else
    VERIFICATION_OK=$((VERIFICATION_OK + 1))
  fi
done

if [ $VERIFICATION_OK -eq ${#VERIFICATION_SCRIPTS[@]} ]; then
  check_pass "All verification scripts present"
fi

# 10. Check that GPT config bundle exists
echo "10. Checking GPT config bundle..."
GPT_CONFIG_FILES=(
  "gpt_config/instructions.txt"
  "gpt_config/starters.md"
  "gpt_config/openapi_url.txt"
  "gpt_config/listing.md"
)

GPT_CONFIG_OK=0
for file in "${GPT_CONFIG_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    check_warn "$file not found (required for GPT deployment)"
  else
    GPT_CONFIG_OK=$((GPT_CONFIG_OK + 1))
  fi
done

if [ $GPT_CONFIG_OK -eq ${#GPT_CONFIG_FILES[@]} ]; then
  check_pass "GPT config bundle complete"
fi

# 11. Check git status (uncommitted changes?)
echo "11. Checking git status..."
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  check_warn "Uncommitted changes detected (commit before deploying)"
else
  check_pass "Git working directory clean"
fi

# 12. Check that main branch is pushed
echo "12. Checking git push status..."
if git status 2>/dev/null | grep -q "Your branch is ahead"; then
  check_warn "Local commits not pushed to origin (git push origin main)"
else
  check_pass "All commits pushed to origin"
fi

# Summary
echo ""
echo "=========================="
echo "📊 SUMMARY"
echo "=========================="
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo ""

if [ $FAIL -gt 0 ]; then
  echo -e "${RED}❌ PRE-DEPLOY CHECK FAILED${NC}"
  echo "Fix the issues above before deploying to Render."
  exit 1
else
  echo -e "${GREEN}✅ PRE-DEPLOY CHECK PASSED${NC}"
  echo ""
  echo "🚀 Ready to deploy!"
  echo ""
  echo "Next steps:"
  echo "1. Go to Render Dashboard"
  echo "2. New + → Blueprint → render-split.yaml"
  echo "3. Mark NEXT_PUBLIC_* vars 'Available during build'"
  echo "4. Set JWT_SECRET and CSRF_SECRET in API service"
  echo "5. Manual Deploy both services"
  echo "6. Run: ./ops/smoke_live.sh --base-url https://your-web-service.onrender.com"
  echo ""
  echo "See docs/RENDER_DEPLOY_QUICKSTART.md for full guide."
  exit 0
fi

