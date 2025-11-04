#!/bin/sh
# Launch Checks Verification Wrapper
# ===================================
# POSIX-compliant shell script to run launch checks and generate reports

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "${GREEN}=== AI-Bookkeeper Launch Checks ===${NC}"
echo

# Load .env if present
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    # Export variables from .env file
    set -a
    . "$ENV_FILE"
    set +a
else
    echo "${YELLOW}Warning: No .env file found at $ENV_FILE${NC}"
    echo "Using environment variables from shell"
fi

# Check required environment variables
if [ -z "$API_BASE" ]; then
    echo "${RED}ERROR: API_BASE environment variable not set${NC}"
    echo "Set it in .env or export it: export API_BASE=https://your-api.com"
    exit 2
fi

if [ -z "$TEST_TENANT_ID" ]; then
    echo "${YELLOW}Warning: TEST_TENANT_ID not set. Some checks may fail.${NC}"
fi

# Generate timestamped output directory
TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
REPORT_DIR="$PROJECT_ROOT/ops/reports/$TIMESTAMP"

echo "Creating report directory: $REPORT_DIR"
mkdir -p "$REPORT_DIR"

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}ERROR: python3 not found in PATH${NC}"
    exit 2
fi

# Check for required Python packages
echo "Checking Python dependencies..."
python3 -c "import requests, yaml" 2>/dev/null || {
    echo "${YELLOW}Warning: Missing dependencies. Install with:${NC}"
    echo "  pip install -U requests pyyaml pytest pydantic jsonschema stripe"
    echo
}

# Run checks
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
OUTPUT_JSON="$REPORT_DIR/report.json"
OUTPUT_MD="$REPORT_DIR/report.md"

echo "Running checks against: $API_BASE"
echo "Config: $CONFIG_FILE"
echo "Output: $OUTPUT_JSON"
echo

# Run Python checks script
cd "$PROJECT_ROOT"
python3 -m ops.launch_checks.checks \
    --config "$CONFIG_FILE" \
    --out "$OUTPUT_JSON"

EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo "${GREEN}✓ All required checks passed!${NC}"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "${RED}✗ One or more required checks failed${NC}"
elif [ $EXIT_CODE -eq 2 ]; then
    echo "${RED}✗ Configuration error${NC}"
else
    echo "${RED}✗ Runtime error${NC}"
fi

echo
echo "Reports generated:"
echo "  JSON: $OUTPUT_JSON"
echo "  Markdown: $OUTPUT_MD"

# Validate JSON schema if jsonschema is available
SCHEMA_FILE="$SCRIPT_DIR/report_schema.json"
if [ -f "$SCHEMA_FILE" ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$OUTPUT_JSON" "$SCHEMA_FILE" <<'PYEOF' 2>/dev/null || {
import sys, json
try:
    import jsonschema
    with open(sys.argv[1]) as f:
        report = json.load(f)
    with open(sys.argv[2]) as f:
        schema = json.load(f)
    jsonschema.validate(report, schema)
    print("✓ Report structure valid")
except ImportError:
    pass  # jsonschema not installed, skip validation
except Exception as e:
    print(f"✗ Schema validation failed: {e}")
    sys.exit(1)
PYEOF
    fi
fi

echo
echo "View full report:"
echo "  cat $OUTPUT_MD"
echo

# Prune old reports: keep last 20
echo "Pruning old reports (keeping last 20)..."
cd "$PROJECT_ROOT/ops/reports"
ls -1dt */ 2>/dev/null | tail -n +21 | xargs -r rm -rf || true

exit $EXIT_CODE

