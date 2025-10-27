#!/usr/bin/env bash
#===============================================================================
# Google Cloud Run Frontend Deployment Script
#===============================================================================
#
# This script automates the deployment of the Next.js frontend to Google Cloud Run.
#
# What It Does:
# ------------
# 1. Creates a Dockerfile for frontend (if missing)
# 2. Builds Docker image using Google Cloud Build
# 3. Pushes image to Artifact Registry
# 4. Deploys to Cloud Run with proper configuration
# 5. Sets environment variables (API_URL)
#
# Requirements:
# ------------
# - gcloud CLI installed and authenticated
# - Google Cloud project with Cloud Run API enabled
# - Artifact Registry repository created
# - Billing enabled on project
#
# Usage:
# ------
# Default (uses environment variables or defaults):
#   ./scripts/deploy_frontend_cloudrun.sh
#
# Custom configuration:
#   PROJECT=my-project \
#   REGION=us-west1 \
#   API_URL=https://my-api.run.app \
#   ./scripts/deploy_frontend_cloudrun.sh
#
# Environment Variables:
# ---------------------
# PROJECT: Google Cloud project ID
# REGION: Cloud Run region (default: us-central1)
# API_URL: Backend API URL for frontend to connect to
#
# Architecture:
# ------------
# - Frontend runs in separate container from backend
# - Frontend makes API calls to backend via API_URL
# - Both services can scale independently
# - Frontend served on port 3000 (mapped to 443 via Cloud Run)
#
#===============================================================================

# Enable strict error handling
# -e: Exit on error
# -u: Error on undefined variable
# -o pipefail: Error if any command in pipe fails
set -euo pipefail

# Print deployment banner
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 GOOGLE CLOUD RUN FRONTEND DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

#===============================================================================
# Configuration - Set deployment parameters
#===============================================================================

# Google Cloud project ID
# Override: PROJECT=my-project ./deploy_frontend_cloudrun.sh
PROJECT="${PROJECT:-bright-fastness-475700-j2}"

# Cloud Run region (us-central1 = Iowa data center)
# Override: REGION=us-west1 ./deploy_frontend_cloudrun.sh
REGION="${REGION:-us-central1}"

# Backend API URL - Frontend connects to this
# Must be set to Cloud Run API URL or custom domain
API_URL="${API_URL:-https://ai-bookkeeper-api-644842661403.us-central1.run.app}"

# Print configuration for verification
echo "📋 Configuration"
echo "  Project: $PROJECT"
echo "  Region: $REGION"
echo "  API URL: $API_URL"
echo ""

#===============================================================================
# Step 1: Create Dockerfile for Frontend (if missing)
#===============================================================================
# This creates a minimal Dockerfile optimized for Next.js production deployment

if [ ! -f "frontend/Dockerfile" ]; then
    echo "📝 Creating frontend/Dockerfile..."
    
    # Generate Dockerfile with heredoc
    # This Dockerfile:
    # 1. Uses Node.js 20 Alpine (minimal size)
    # 2. Installs dependencies
    # 3. Builds Next.js for production
    # 4. Runs production server on port 3000
    cat > frontend/Dockerfile << 'DOCKEREOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build
ENV PORT=3000
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "run", "start"]
DOCKEREOF
    
    echo "✅ Dockerfile created"
fi

echo ""
echo "🔨 Building and deploying frontend..."
echo ""

#===============================================================================
# Step 2: Build Docker Image with Cloud Build
#===============================================================================
# Google Cloud Build:
# - Reads Dockerfile from frontend/
# - Builds image in cloud (faster, more resources)
# - Pushes to Artifact Registry automatically
# - Tags as "latest" for easy updates

gcloud builds submit ./frontend \
  --tag "${REGION}-docker.pkg.dev/${PROJECT}/app/web:latest" \
  --project "$PROJECT"

echo ""
echo "🚀 Deploying to Cloud Run..."
echo ""

gcloud run deploy ai-bookkeeper-web \
  --image "${REGION}-docker.pkg.dev/${PROJECT}/app/web:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 3000 \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi \
  --set-env-vars "NEXT_PUBLIC_API_URL=${API_URL}" \
  --project "$PROJECT"

# Get the URL
WEB_URL=$(gcloud run services describe ai-bookkeeper-web \
  --region "$REGION" \
  --project "$PROJECT" \
  --format='value(status.url)')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Frontend URL: $WEB_URL"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Update CORS on API:"
echo "   cat > tmp/env_vars.yaml << CORSEOF"
echo "   ALLOWED_ORIGINS: \"https://app.ai-bookkeeper.app,$WEB_URL\""
echo "   CORSEOF"
echo ""
echo "   gcloud run services update ai-bookkeeper-api \\"
echo "     --region $REGION \\"
echo "     --env-vars-file tmp/env_vars.yaml \\"
echo "     --quiet"
echo ""
echo "2. Run smoke tests:"
echo "   bash scripts/smoke_cutover.sh \\"
echo "     \"$API_URL\" \\"
echo "     \"$WEB_URL\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Save URL
mkdir -p tmp
echo "$WEB_URL" > tmp/WEB_URL.txt
echo "✅ Web URL saved to tmp/WEB_URL.txt"
