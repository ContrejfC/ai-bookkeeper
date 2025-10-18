#!/bin/bash
# ============================================================================
# AI Bookkeeper - LIVE Launch Script
# ============================================================================
# Single entrypoint for production launch verification and API key generation
# Run this on Render API service shell after deploying with LIVE credentials
# ============================================================================

set -e  # Exit on first error

echo "============================================================================"
echo "  AI Bookkeeper - LIVE Launch Verification"
echo "============================================================================"
echo ""

# ============================================================================
# Step 1: Verify Production Environment
# ============================================================================
echo "📋 Step 1: Verifying production environment variables..."
echo ""

if ! python3 scripts/verify_prod_env.py; then
    echo ""
    echo "❌ FAILED: Production environment variables not set correctly"
    echo "   Fix: Set all required env vars in Render Dashboard"
    echo "   See: docs/GO_LIVE_NOW.md for complete list"
    exit 1
fi

echo "✅ Production environment verified"
echo ""

# ============================================================================
# Step 2: Verify QBO Production Configuration
# ============================================================================
echo "📋 Step 2: Verifying QBO production configuration..."
echo ""

if ! python3 scripts/check_qbo_env.py; then
    echo ""
    echo "❌ FAILED: QBO not configured for production"
    echo "   Fix: Set QBO_CLIENT_ID, QBO_CLIENT_SECRET to production values"
    echo "   Fix: Set QBO_BASE=https://quickbooks.api.intuit.com"
    echo "   See: docs/GO_LIVE_NOW.md for details"
    exit 1
fi

echo "✅ QBO production configuration verified"
echo ""

# ============================================================================
# Step 3: Verify Stripe LIVE Configuration
# ============================================================================
echo "📋 Step 3: Verifying Stripe LIVE configuration..."
echo ""

# Install stripe if not present
pip install -q stripe 2>/dev/null || true

if ! python3 scripts/verify_stripe_webhook.py; then
    echo ""
    echo "⚠️  WARNING: Stripe webhook verification failed"
    echo "   This is OK if webhook is not yet configured"
    echo "   You can configure it after launch"
    echo ""
else
    echo "✅ Stripe LIVE webhook verified"
    echo ""
fi

# ============================================================================
# Step 4: Generate Production API Key
# ============================================================================
echo "📋 Step 4: Generating production API key for GPT Actions..."
echo ""

# Create ops directory if it doesn't exist
mkdir -p ops

# Generate API key and save to file
if python3 scripts/create_api_key.py --tenant production --name "GPT Live" > ops/.last_api_key.txt 2>&1; then
    echo "✅ Production API key generated"
    echo ""
    
    # Extract the API key
    API_KEY=$(grep -o 'ak_[a-zA-Z0-9_-]*' ops/.last_api_key.txt | head -1)
    
    if [ -z "$API_KEY" ]; then
        echo "❌ FAILED: Could not extract API key from output"
        echo "   Check ops/.last_api_key.txt for details"
        exit 1
    fi
    
    echo "🔑 API Key: $API_KEY"
    echo "   (Saved to: ops/.last_api_key.txt)"
    echo ""
else
    echo "❌ FAILED: Could not generate API key"
    echo "   Check ops/.last_api_key.txt for error details"
    exit 1
fi

# ============================================================================
# Step 5: Run Production Smoke Tests
# ============================================================================
echo "📋 Step 5: Running production smoke tests..."
echo ""

# Determine base URL
if [ -z "$PUBLIC_BASE_URL" ]; then
    PUBLIC_BASE_URL="https://ai-bookkeeper.onrender.com"
    echo "⚠️  PUBLIC_BASE_URL not set, using default: $PUBLIC_BASE_URL"
fi

# Run comprehensive smoke tests
if ./ops/smoke_live.sh \
    --base-url "$PUBLIC_BASE_URL" \
    --api-key "$API_KEY" \
    --use-sample-je \
    --spec-version v1.0; then
    echo ""
    echo "✅ All smoke tests PASSED"
else
    echo ""
    echo "❌ FAILED: Smoke tests did not pass"
    echo "   Check output above for details"
    exit 1
fi

# ============================================================================
# Success Summary
# ============================================================================
echo ""
echo "============================================================================"
echo "  ✅ LIVE LAUNCH VERIFICATION COMPLETE"
echo "============================================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure ChatGPT GPT with Actions:"
echo "   - OpenAPI URL: $PUBLIC_BASE_URL/openapi.json"
echo "   - Auth: API Key (Bearer)"
echo "   - Authorization Header: Bearer $API_KEY"
echo ""
echo "2. Follow the GPT publish checklist:"
echo "   - See: gpt_config/public_publish_checklist.md"
echo ""
echo "3. Copy/paste for GPT Builder:"
echo "   Authorization: Bearer $API_KEY"
echo ""
echo "4. Full launch guide:"
echo "   - See: docs/GO_LIVE_NOW.md"
echo ""
echo "============================================================================"
echo ""

# Save summary for reference
cat > ops/.launch_summary.txt <<EOF
Launch Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Base URL: $PUBLIC_BASE_URL
OpenAPI URL: $PUBLIC_BASE_URL/openapi.json
API Key: $API_KEY
Status: SUCCESS

Next: Configure GPT Actions in ChatGPT GPT Builder
      See: gpt_config/public_publish_checklist.md
EOF

echo "📝 Launch summary saved to: ops/.launch_summary.txt"
echo ""

exit 0

