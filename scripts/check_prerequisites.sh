#!/usr/bin/env bash
# Prerequisites Checker for Google Cloud Run Migration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🔍 GOOGLE CLOUD RUN MIGRATION PREREQUISITES CHECK"
echo "=================================================="

# Check system requirements
print_status "INFO" "Checking system requirements..."

# Check OS
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "SUCCESS" "OS supported: $OSTYPE"
else
    print_status "ERROR" "Unsupported OS: $OSTYPE (Linux/macOS required)"
    exit 1
fi

# Check required tools
print_status "INFO" "Checking required tools..."

tools=("bash" "curl" "jq" "python3" "gcloud")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        version=$($tool --version 2>/dev/null | head -1 || echo "unknown")
        print_status "SUCCESS" "$tool: $version"
    else
        print_status "ERROR" "$tool: Not installed"
        echo "  Install with:"
        case $tool in
            "gcloud")
                echo "    curl https://sdk.cloud.google.com | bash"
                echo "    exec -l $SHELL"
                ;;
            "jq")
                echo "    # macOS: brew install jq"
                echo "    # Ubuntu: sudo apt-get install jq"
                echo "    # CentOS: sudo yum install jq"
                ;;
        esac
    fi
done

# Check environment variables
print_status "INFO" "Checking environment variables..."

required_vars=(
    "PROJECT:Google Cloud Project ID"
    "REGION:GCP Region (e.g., us-central1)"
    "GCP_SA_JSON_PATH:Path to service account JSON key"
    "WEB_ORIGINS:Comma-separated web origins for CORS"
    "JWT_SECRET:JWT signing secret"
)

for var_info in "${required_vars[@]}"; do
    var_name="${var_info%%:*}"
    var_desc="${var_info#*:}"
    
    if [[ -n "${!var_name:-}" ]]; then
        print_status "SUCCESS" "$var_name: Set"
    else
        print_status "ERROR" "$var_name: Not set ($var_desc)"
    fi
done

# Check optional variables
print_status "INFO" "Checking optional variables..."

optional_vars=(
    "DB_URL:Database connection string"
    "MIGRATE_WEB:Whether to migrate web service (true/false)"
    "CLOUD_SQL:Whether to use Cloud SQL (true/false)"
    "CLOUDFLARE_API_TOKEN:Cloudflare API token for DNS automation"
    "CLOUDFLARE_ZONE_ID:Cloudflare zone ID"
    "DOMAIN_ROOT:Root domain (e.g., ai-bookkeeper.app)"
)

for var_info in "${optional_vars[@]}"; do
    var_name="${var_info%%:*}"
    var_desc="${var_info#*:}"
    
    if [[ -n "${!var_name:-}" ]]; then
        print_status "SUCCESS" "$var_name: Set"
    else
        print_status "WARNING" "$var_name: Not set ($var_desc)"
    fi
done

# Check service account file
if [[ -n "${GCP_SA_JSON_PATH:-}" ]]; then
    if [[ -f "$GCP_SA_JSON_PATH" ]]; then
        print_status "SUCCESS" "Service account file exists: $GCP_SA_JSON_PATH"
        
        # Check if it's valid JSON
        if jq empty "$GCP_SA_JSON_PATH" 2>/dev/null; then
            print_status "SUCCESS" "Service account file is valid JSON"
            
            # Check required fields
            if jq -e '.type' "$GCP_SA_JSON_PATH" >/dev/null 2>&1; then
                sa_type=$(jq -r '.type' "$GCP_SA_JSON_PATH")
                print_status "SUCCESS" "Service account type: $sa_type"
            fi
            
            if jq -e '.project_id' "$GCP_SA_JSON_PATH" >/dev/null 2>&1; then
                sa_project=$(jq -r '.project_id' "$GCP_SA_JSON_PATH")
                print_status "SUCCESS" "Service account project: $sa_project"
            fi
        else
            print_status "ERROR" "Service account file is not valid JSON"
        fi
    else
        print_status "ERROR" "Service account file not found: $GCP_SA_JSON_PATH"
    fi
fi

# Check gcloud authentication
if command -v gcloud &> /dev/null; then
    print_status "INFO" "Checking gcloud authentication..."
    
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
        print_status "SUCCESS" "Active gcloud account: $active_account"
    else
        print_status "WARNING" "No active gcloud authentication"
        print_status "INFO" "Will authenticate with service account during migration"
    fi
    
    # Check if project is set
    if gcloud config get-value project &>/dev/null; then
        current_project=$(gcloud config get-value project)
        print_status "SUCCESS" "Current gcloud project: $current_project"
    else
        print_status "WARNING" "No gcloud project configured"
    fi
fi

echo ""
echo "📋 SETUP INSTRUCTIONS"
echo "====================="

echo ""
echo "1. Install missing tools (if any):"
echo "   gcloud: curl https://sdk.cloud.google.com | bash"
echo "   jq: brew install jq (macOS) or sudo apt-get install jq (Ubuntu)"

echo ""
echo "2. Set required environment variables:"
echo "   export PROJECT=your-gcp-project-id"
echo "   export REGION=us-central1"
echo "   export GCP_SA_JSON_PATH=/path/to/service-account.json"
echo "   export WEB_ORIGINS=\"https://app.ai-bookkeeper.app,https://your-web-domain.com\""
echo "   export JWT_SECRET=your-jwt-secret"

echo ""
echo "3. Set optional environment variables:"
echo "   export DB_URL=\"postgresql://user:pass@host:port/db\""
echo "   export MIGRATE_WEB=true"
echo "   export CLOUD_SQL=false"
echo "   export CLOUDFLARE_API_TOKEN=your-cloudflare-token"
echo "   export CLOUDFLARE_ZONE_ID=your-zone-id"
echo "   export DOMAIN_ROOT=ai-bookkeeper.app"

echo ""
echo "4. Create service account with required roles:"
echo "   - Cloud Run Admin (run.admin)"
echo "   - Cloud Build Editor (cloudbuild.builds.editor)"
echo "   - Artifact Registry Writer (artifactregistry.writer)"
echo "   - Secret Manager Admin (secretmanager.admin)"
echo "   - Service Account User (iam.serviceAccountUser)"
echo "   - Cloud SQL Admin (sql.admin) - if CLOUD_SQL=true"

echo ""
echo "5. Run migration:"
echo "   bash scripts/gcp_migrate.sh"

echo ""
print_status "INFO" "Prerequisites check complete!"
