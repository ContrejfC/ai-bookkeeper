#!/usr/bin/env bash
#
# AI Bookkeeper MVP - Deploy to Google Cloud Platform
# ====================================================
#
# This script deploys the complete MVP to Google Cloud Run
# with all the new features: paywall, onboarding, QBO sandbox, etc.
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Project created in GCP
# - Billing enabled
# - APIs enabled: Cloud Run, Cloud Build, Artifact Registry

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   AI Bookkeeper MVP - Google Cloud Deployment            ║
║                                                           ║
║   Deploying:                                              ║
║   ✅ Backend API (FastAPI)                               ║
║   ✅ Frontend (Next.js)                                  ║
║   ✅ Paywall Enforcement                                 ║
║   ✅ Onboarding Flow                                     ║
║   ✅ QBO Sandbox Support                                 ║
║   ✅ All 110 Tests                                       ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ============================================================================
# Configuration
# ============================================================================

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get or set project
if [[ -z "${PROJECT:-}" ]]; then
    echo -e "${YELLOW}📋 Select GCP Project${NC}"
    PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [[ -z "$PROJECT" ]]; then
        echo "No project configured. Please set:"
        echo "  export PROJECT=your-gcp-project-id"
        exit 1
    fi
    
    echo -e "${GREEN}Using project: $PROJECT${NC}"
fi

# Set region
REGION="${REGION:-us-central1}"
echo -e "${GREEN}Using region: $REGION${NC}"

# Service names
API_SERVICE="ai-bookkeeper-api-mvp"
WEB_SERVICE="ai-bookkeeper-web-mvp"

# Docker image names
API_IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/ai-bookkeeper/api:mvp-latest"
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/ai-bookkeeper/web:mvp-latest"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Project: $PROJECT"
echo "  Region: $REGION"
echo "  API Service: $API_SERVICE"
echo "  Web Service: $WEB_SERVICE"
echo ""

# ============================================================================
# Step 1: Enable Required APIs
# ============================================================================

echo -e "${BLUE}Step 1/6: Enabling Google Cloud APIs...${NC}"

gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project="$PROJECT" \
    2>&1 | grep -v "already enabled" || true

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# ============================================================================
# Step 2: Create Artifact Registry Repository
# ============================================================================

echo -e "${BLUE}Step 2/6: Creating Artifact Registry repository...${NC}"

gcloud artifacts repositories create ai-bookkeeper \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT" \
    2>&1 | grep -v "already exists" || true

echo -e "${GREEN}✅ Artifact Registry ready${NC}"
echo ""

# ============================================================================
# Step 3: Build and Push Backend Image
# ============================================================================

echo -e "${BLUE}Step 3/6: Building and pushing backend image...${NC}"
echo "This may take 5-10 minutes..."

# Build backend
gcloud builds submit . \
    --tag="$API_IMAGE" \
    --project="$PROJECT" \
    --timeout=20m \
    --machine-type=e2-highcpu-8

echo -e "${GREEN}✅ Backend image built and pushed${NC}"
echo ""

# ============================================================================
# Step 4: Deploy Backend to Cloud Run
# ============================================================================

echo -e "${BLUE}Step 4/6: Deploying backend to Cloud Run...${NC}"

# Get environment variables (use existing or defaults)
DATABASE_URL="${DATABASE_URL:-sqlite:///./aibookkeeper.db}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
QBO_ENV="${QBO_ENV:-sandbox}"
DEMO_MODE="${DEMO_MODE:-true}"

gcloud run deploy "$API_SERVICE" \
    --image="$API_IMAGE" \
    --region="$REGION" \
    --project="$PROJECT" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --min-instances=0 \
    --max-instances=10 \
    --cpu=2 \
    --memory=1Gi \
    --timeout=300 \
    --set-env-vars="DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,QBO_ENV=$QBO_ENV,DEMO_MODE=$DEMO_MODE" \
    --set-env-vars="STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY" \
    2>&1

# Get API URL
API_URL=$(gcloud run services describe "$API_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT" \
    --format='value(status.url)')

echo -e "${GREEN}✅ Backend deployed${NC}"
echo -e "${GREEN}   URL: $API_URL${NC}"
echo ""

# Save API URL
mkdir -p tmp
echo "$API_URL" > tmp/API_URL.txt

# ============================================================================
# Step 5: Build and Push Frontend Image
# ============================================================================

echo -e "${BLUE}Step 5/6: Building and pushing frontend image...${NC}"
echo "This may take 10-15 minutes..."

# Build frontend with API URL
cd frontend

# Create .env.production
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=$API_URL
NEXT_PUBLIC_BASE_URL=https://TBD
EOF

cd ..

# Build frontend
gcloud builds submit ./frontend \
    --tag="$WEB_IMAGE" \
    --project="$PROJECT" \
    --timeout=20m \
    --machine-type=e2-highcpu-8

echo -e "${GREEN}✅ Frontend image built and pushed${NC}"
echo ""

# ============================================================================
# Step 6: Deploy Frontend to Cloud Run
# ============================================================================

echo -e "${BLUE}Step 6/6: Deploying frontend to Cloud Run...${NC}"

gcloud run deploy "$WEB_SERVICE" \
    --image="$WEB_IMAGE" \
    --region="$REGION" \
    --project="$PROJECT" \
    --platform=managed \
    --allow-unauthenticated \
    --port=3000 \
    --min-instances=0 \
    --max-instances=10 \
    --cpu=1 \
    --memory=512Mi \
    --timeout=60 \
    --set-env-vars="NEXT_PUBLIC_API_URL=$API_URL" \
    2>&1

# Get Web URL
WEB_URL=$(gcloud run services describe "$WEB_SERVICE" \
    --region="$REGION" \
    --project="$PROJECT" \
    --format='value(status.url)')

echo -e "${GREEN}✅ Frontend deployed${NC}"
echo -e "${GREEN}   URL: $WEB_URL${NC}"
echo ""

# Save Web URL
echo "$WEB_URL" > tmp/WEB_URL.txt

# ============================================================================
# Deployment Summary
# ============================================================================

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 DEPLOYMENT SUCCESSFUL!                              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Service URLs:${NC}"
echo ""
echo -e "  ${GREEN}Backend API:${NC}"
echo -e "    $API_URL"
echo ""
echo -e "  ${GREEN}Frontend:${NC}"
echo -e "    $WEB_URL"
echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo ""
echo "  1. Test the health endpoint:"
echo -e "     ${YELLOW}curl $API_URL/healthz${NC}"
echo ""
echo "  2. Open the frontend:"
echo -e "     ${YELLOW}open $WEB_URL${NC}"
echo ""
echo "  3. Run smoke tests:"
echo -e "     ${YELLOW}./scripts/smoke_tests_gcp.sh${NC}"
echo ""
echo "  4. Configure environment variables:"
echo -e "     - Stripe keys (for billing)"
echo -e "     - QBO credentials (for sandbox/production)"
echo -e "     - Database URL (for PostgreSQL)"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "  - RUNBOOK_MVP.md - Operations guide"
echo "  - MVP_ACCEPTANCE_REPORT.md - Validation results"
echo "  - MVP_FINAL_COMPLETE.md - Complete implementation guide"
echo ""
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "  - Set up custom domain (optional)"
echo "  - Configure Stripe webhooks"
echo "  - Set up Cloud Monitoring alerts"
echo "  - Enable Cloud SQL for production database"
echo ""
echo -e "${GREEN}✅ MVP is now live on Google Cloud!${NC}"
echo ""

# Save deployment info
cat > tmp/gcp_deployment_info.txt << EOF
AI Bookkeeper MVP - Google Cloud Deployment
===========================================

Deployed: $(date)
Project: $PROJECT
Region: $REGION

Services:
---------
Backend API:  $API_URL
Frontend Web: $WEB_URL

Images:
-------
API: $API_IMAGE
Web: $WEB_IMAGE

Status: ✅ DEPLOYED

Next Steps:
-----------
1. Test health endpoint: curl $API_URL/healthz
2. Open frontend: $WEB_URL
3. Run smoke tests
4. Configure production environment variables
5. Set up monitoring and alerts

Documentation:
--------------
- RUNBOOK_MVP.md
- MVP_ACCEPTANCE_REPORT.md
- MVP_FINAL_COMPLETE.md
EOF

echo -e "${GREEN}💾 Deployment info saved to tmp/gcp_deployment_info.txt${NC}"
echo ""

