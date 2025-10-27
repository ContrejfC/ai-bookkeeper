#!/usr/bin/env bash
# Google Cloud Run Migration Script
# Migrates AI Bookkeeper from Render to Google Cloud Run

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [[ $status == "SUCCESS" ]]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [[ $status == "ERROR" ]]; then
        echo -e "${RED}❌ $message${NC}"
    elif [[ $status == "WARNING" ]]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "INFO" "Checking prerequisites..."
    
    # Check required tools
    local tools=("bash" "curl" "jq" "python3" "gcloud")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_status "ERROR" "Missing required tool: $tool"
            exit 1
        fi
    done
    
    # Check required environment variables
    local required_vars=("PROJECT" "REGION" "GCP_SA_JSON_PATH" "WEB_ORIGINS" "JWT_SECRET")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            print_status "ERROR" "Required environment variable not set: $var"
            print_status "INFO" "Please export $var=your_value"
            exit 1
        fi
    done
    
    # Check optional variables
    MIGRATE_WEB="${MIGRATE_WEB:-false}"
    CLOUD_SQL="${CLOUD_SQL:-false}"
    
    print_status "SUCCESS" "All prerequisites met"
}

# Function to authenticate and setup GCP
setup_gcp() {
    print_status "INFO" "Setting up Google Cloud Platform..."
    
    # Authenticate with service account
    gcloud auth activate-service-account --key-file "$GCP_SA_JSON_PATH"
    gcloud config set project "$PROJECT"
    
    # Enable required services
    gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
    
    if [[ "$CLOUD_SQL" == "true" ]]; then
        gcloud services enable sqladmin.googleapis.com
        print_status "INFO" "Cloud SQL services enabled"
    fi
    
    print_status "SUCCESS" "GCP setup complete"
}

# Function to manage secrets
manage_secrets() {
    print_status "INFO" "Managing secrets in Secret Manager..."
    
    # List of secrets to create
    local secrets=("JWT_SECRET" "STRIPE_SECRET" "STRIPE_WEBHOOK_SECRET" "OPENAI_API_KEY")
    
    for secret_name in "${secrets[@]}"; do
        local secret_value="${!secret_name:-}"
        if [[ -n "$secret_value" ]]; then
            print_status "INFO" "Creating secret: $secret_name"
            gcloud secrets create "$secret_name" || true
            printf "%s" "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
        fi
    done
    
    print_status "SUCCESS" "Secrets management complete"
}

# Function to deploy API
deploy_api() {
    print_status "INFO" "Deploying API to Cloud Run..."
    
    bash scripts/gcp_deploy_api.sh
    
    # Export API_URL
    export API_URL="$(cat tmp/API_URL.txt)"
    print_status "SUCCESS" "API deployed successfully"
    print_status "INFO" "API URL: $API_URL"
}

# Function to deploy web (optional)
deploy_web() {
    if [[ "$MIGRATE_WEB" == "true" ]]; then
        print_status "INFO" "Deploying Web to Cloud Run..."
        
        bash scripts/gcp_deploy_web.sh
        
        # Export WEB_URL
        export WEB_URL="$(cat tmp/WEB_URL.txt)"
        print_status "SUCCESS" "Web deployed successfully"
        print_status "INFO" "Web URL: $WEB_URL"
    else
        print_status "INFO" "Skipping web deployment (MIGRATE_WEB=false)"
        export WEB_URL="https://app.ai-bookkeeper.app"
    fi
}

# Function to configure DNS
configure_dns() {
    print_status "INFO" "Configuring DNS..."
    
    if [[ -n "${CLOUDFLARE_API_TOKEN:-}" && -n "${CLOUDFLARE_ZONE_ID:-}" ]]; then
        print_status "INFO" "Automated DNS configuration with Cloudflare..."
        
        # API CNAME
        local api_host=$(echo "$API_URL" | sed -E 's#https?://##')
        curl -sX POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
            -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"CNAME\",\"name\":\"api.${DOMAIN_ROOT:-ai-bookkeeper.app}\",\"content\":\"${api_host}\",\"ttl\":120,\"proxied\":false}" \
            | jq -r '.result.id' > /dev/null
        
        print_status "SUCCESS" "API DNS record created: api.${DOMAIN_ROOT:-ai-bookkeeper.app}"
        
        # Web CNAME (if migrated)
        if [[ "$MIGRATE_WEB" == "true" ]]; then
            local web_host=$(echo "$WEB_URL" | sed -E 's#https?://##')
            curl -sX POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
                -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
                -H "Content-Type: application/json" \
                --data "{\"type\":\"CNAME\",\"name\":\"app.${DOMAIN_ROOT:-ai-bookkeeper.app}\",\"content\":\"${web_host}\",\"ttl\":120,\"proxied\":false}" \
                | jq -r '.result.id' > /dev/null
            
            print_status "SUCCESS" "Web DNS record created: app.${DOMAIN_ROOT:-ai-bookkeeper.app}"
        fi
    else
        print_status "WARNING" "Manual DNS configuration required"
        print_status "INFO" "Create CNAME records:"
        print_status "INFO" "  api.${DOMAIN_ROOT:-ai-bookkeeper.app} → $(echo "$API_URL" | sed -E 's#https?://##')"
        if [[ "$MIGRATE_WEB" == "true" ]]; then
            print_status "INFO" "  app.${DOMAIN_ROOT:-ai-bookkeeper.app} → $(echo "$WEB_URL" | sed -E 's#https?://##')"
        fi
    fi
}

# Function to run smoke tests
run_smoke_tests() {
    print_status "INFO" "Running smoke tests..."
    
    bash scripts/smoke.sh
    
    print_status "SUCCESS" "Smoke tests passed"
}

# Function to create deployment summary
create_summary() {
    print_status "INFO" "Creating deployment summary..."
    
    cat > DEPLOY_SUMMARY.md << EOF
# Google Cloud Run Migration Summary

**Deployment Date:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')
**Project:** $PROJECT
**Region:** $REGION

## 🚀 Deployed Services

### API Service
- **Name:** ai-bookkeeper-api
- **URL:** $API_URL
- **Health Check:** $API_URL/healthz
- **Environment Variables:**
  - ALLOWED_ORIGINS: $WEB_ORIGINS
  - DATABASE_URL: ${DB_URL:-"Not set"}
  - JWT_SECRET: Set via Secret Manager

### Web Service
- **Name:** ai-bookkeeper-web
- **URL:** $WEB_URL
- **Migrated:** $MIGRATE_WEB
- **Environment Variables:**
  - NEXT_PUBLIC_API_URL: $API_URL

## 🌐 DNS Configuration

### Automated (if Cloudflare token provided)
- api.${DOMAIN_ROOT:-ai-bookkeeper.app} → API service
- app.${DOMAIN_ROOT:-ai-bookkeeper.app} → Web service (if migrated)

### Manual (if no Cloudflare token)
Create CNAME records:
- api.${DOMAIN_ROOT:-ai-bookkeeper.app} → $(echo "$API_URL" | sed -E 's#https?://##')
- app.${DOMAIN_ROOT:-ai-bookkeeper.app} → $(echo "$WEB_URL" | sed -E 's#https?://##')

## 🔧 Next Steps

1. **Wait for DNS propagation** (5-10 minutes)
2. **Update CORS origins** after DNS cutover:
   \`\`\`bash
   gcloud run services update ai-bookkeeper-api --region "$REGION" --set-env-vars "ALLOWED_ORIGINS=https://app.${DOMAIN_ROOT:-ai-bookkeeper.app},https://$(echo "$WEB_URL" | sed -E 's#https?://##')"
   \`\`\`
3. **Test end-to-end functionality**
4. **Update frontend** to use new API URL
5. **Monitor service health**

## 🔄 Rollback Instructions

If issues occur:
1. **Point DNS back** to previous endpoints
2. **Fix issues** in Cloud Run services
3. **Redeploy** with fixes
4. **Retry DNS cutover**

## 📊 Service Configuration

- **Min Instances:** 1 (prevents cold starts)
- **Max Instances:** 10
- **CPU:** 1 vCPU
- **Memory:** 512Mi
- **Port:** 8080 (API), 3000 (Web)

## 🔐 Security

- **Authentication:** Service Account with minimal permissions
- **Secrets:** Managed via Google Secret Manager
- **CORS:** Configured for specified origins
- **HTTPS:** Enabled by default

## 📈 Monitoring

Monitor services at:
- [Cloud Run Console](https://console.cloud.google.com/run)
- [Cloud Build Console](https://console.cloud.google.com/cloud-build)
- [Secret Manager Console](https://console.cloud.google.com/security/secret-manager)

EOF

    print_status "SUCCESS" "Deployment summary created: DEPLOY_SUMMARY.md"
}

# Main execution
main() {
    print_status "INFO" "Starting Google Cloud Run migration..."
    print_status "INFO" "Project: $PROJECT"
    print_status "INFO" "Region: $REGION"
    print_status "INFO" "Migrate Web: $MIGRATE_WEB"
    print_status "INFO" "Cloud SQL: $CLOUD_SQL"
    
    check_prerequisites
    setup_gcp
    manage_secrets
    deploy_api
    deploy_web
    configure_dns
    run_smoke_tests
    create_summary
    
    print_status "SUCCESS" "Migration completed successfully!"
    print_status "INFO" "API URL: $API_URL"
    print_status "INFO" "Web URL: $WEB_URL"
    
    if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
        print_status "WARNING" "Manual DNS configuration required"
        print_status "INFO" "After DNS propagation, update CORS:"
        print_status "INFO" "gcloud run services update ai-bookkeeper-api --region $REGION --set-env-vars 'ALLOWED_ORIGINS=$WEB_ORIGINS'"
    fi
}

# Run main function
main "$@"






