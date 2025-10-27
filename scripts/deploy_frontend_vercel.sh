#!/usr/bin/env bash
set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 VERCEL FRONTEND DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

API_URL="${API_URL:-https://ai-bookkeeper-api-644842661403.us-central1.run.app}"

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found"
    echo ""
    echo "Install it with:"
    echo "  npm install -g vercel"
    echo ""
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Check if in frontend directory
if [ ! -f "package.json" ]; then
    if [ -d "frontend" ]; then
        echo "📁 Changing to frontend directory..."
        cd frontend
    else
        echo "❌ frontend directory not found"
        exit 1
    fi
fi

echo "📋 Frontend Configuration"
echo "  API URL: $API_URL"
echo ""

# Create .env.production file
echo "📝 Creating .env.production..."
cat > .env.production << ENVEOF
NEXT_PUBLIC_API_URL=$API_URL
ENVEOF

echo "✅ Environment file created"
echo ""

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
echo ""
echo "Please follow the prompts to:"
echo "1. Link to existing project or create new"
echo "2. Choose production deployment"
echo ""

vercel --prod

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Note your Vercel URL from above"
echo "2. Update CORS on API:"
echo "   cat > tmp/env_vars.yaml << CORSEOF"
echo "   ALLOWED_ORIGINS: \"https://app.ai-bookkeeper.app,https://YOUR-VERCEL-URL\""
echo "   CORSEOF"
echo ""
echo "   gcloud run services update ai-bookkeeper-api \\"
echo "     --region us-central1 \\"
echo "     --env-vars-file tmp/env_vars.yaml \\"
echo "     --quiet"
echo ""
echo "3. Run smoke tests:"
echo "   bash scripts/smoke_cutover.sh \\"
echo "     \"$API_URL\" \\"
echo "     \"https://YOUR-VERCEL-URL\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
