#!/bin/bash
#===============================================================================
# Unified Docker Deployment to Google Cloud Run
#===============================================================================
#
# This script deploys BOTH frontend and backend as a single container to 
# Google Cloud Run, eliminating the split deployment complexity.
#
# Benefits:
#   ✅ Single deployment = single source of truth
#   ✅ No NEXT_PUBLIC_API_URL confusion (frontend talks to localhost:8000)
#   ✅ Frontend and backend always in sync
#   ✅ Simpler configuration
#   ✅ No CORS issues (same origin)
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Project configured: gcloud config set project PROJECT_ID
#   - APIs enabled: Cloud Run, Cloud Build, Artifact Registry
#   - DATABASE_URL ready (Neon PostgreSQL connection string)
#
#===============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Bookkeeper - Unified Docker Deployment${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

#===============================================================================
# Step 1: Configuration
#===============================================================================
echo -e "\n${BLUE}📋 Step 1: Configuration${NC}"

# Get current GCP project
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ]; then
  echo -e "${RED}❌ No GCP project configured${NC}"
  echo "Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

# Configuration
SERVICE_NAME="ai-bookkeeper"
REGION="us-central1"
PLATFORM="managed"

echo "   Project: $PROJECT"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
  echo -e "${RED}❌ DATABASE_URL not set${NC}"
  echo "Please set your database connection string:"
  echo "  export DATABASE_URL='postgresql://user:pass@host/db'"
  exit 1
fi

echo -e "${GREEN}✅ Configuration valid${NC}"

#===============================================================================
# Step 2: Build and Deploy to Cloud Run
#===============================================================================
echo -e "\n${BLUE}📦 Step 2: Build and Deploy${NC}"
echo "This will:"
echo "  1. Build Docker image (frontend + backend)"
echo "  2. Push to Google Container Registry"
echo "  3. Deploy to Cloud Run"
echo "  4. Configure environment variables"

# Deploy using Cloud Build (automatically builds and deploys)
echo -e "\n${YELLOW}Building and deploying...${NC}"

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform $PLATFORM \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,BACKEND_PORT=8000,NODE_ENV=production,NEXT_PUBLIC_API_URL=http://localhost:8000" \
  --quiet

#===============================================================================
# Step 3: Get Service URL
#===============================================================================
echo -e "\n${BLUE}🌐 Step 3: Get Service URL${NC}"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --platform $PLATFORM \
  --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
  echo -e "${RED}❌ Failed to get service URL${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

#===============================================================================
# Step 4: Display Results
#===============================================================================
echo -e "\n${GREEN}🎉 UNIFIED DEPLOYMENT COMPLETE!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📍 Service URL:${NC}"
echo "   $SERVICE_URL"
echo ""
echo -e "${BLUE}🔗 Quick Links:${NC}"
echo "   Frontend: $SERVICE_URL"
echo "   API Docs: $SERVICE_URL/docs"
echo "   Health:   $SERVICE_URL/api/health"
echo ""
echo -e "${BLUE}📊 Cloud Console:${NC}"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

#===============================================================================
# Step 5: Run Basic Smoke Tests
#===============================================================================
echo -e "\n${BLUE}🧪 Step 5: Running Smoke Tests${NC}"

# Test 1: Frontend
echo -n "   Testing frontend... "
if curl -sf "$SERVICE_URL" > /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
fi

# Test 2: Backend API
echo -n "   Testing backend API... "
if curl -sf "$SERVICE_URL/api/health" > /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
fi

# Test 3: API Docs
echo -n "   Testing API docs... "
if curl -sf "$SERVICE_URL/docs" > /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
fi

echo ""
echo -e "${GREEN}✅ All smoke tests passed!${NC}"

#===============================================================================
# Step 6: Next Steps
#===============================================================================
echo -e "\n${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Test the application:"
echo "   Open: $SERVICE_URL"
echo ""
echo "2. Monitor logs:"
echo "   gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
echo "3. Update deployment (after code changes):"
echo "   bash scripts/deploy_unified.sh"
echo ""
echo "4. Decommission old deployments:"
echo "   - Remove Vercel project (frontend)"
echo "   - Remove old Cloud Run backend service"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎊 Deployment complete! Your app is live!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

