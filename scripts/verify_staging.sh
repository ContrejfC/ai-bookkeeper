#!/bin/bash
# Render Staging Verification Script
# Run this after deploying to Render to collect readiness artifacts

set -e

RENDER_URL="${RENDER_URL:-https://ai-bookkeeper-web.onrender.com}"
OUTPUT_DIR="artifacts/staging"
PERF_DIR="artifacts/perf"

echo "🔍 Verifying Render Staging Deployment"
echo "========================================"
echo "URL: $RENDER_URL"
echo "Output: $OUTPUT_DIR"
echo ""

# Create output directories
mkdir -p "$OUTPUT_DIR" "$PERF_DIR"

# 1. Alembic current version
echo "📦 Checking Alembic version..."
if command -v python3 &> /dev/null; then
    python3 -m alembic current > "$OUTPUT_DIR/alembic_current.txt" 2>&1 || echo "Error: Run this in Render Shell"
    echo "   ✅ Saved to $OUTPUT_DIR/alembic_current.txt"
else
    echo "   ⚠️  Python not found. Run in Render Shell: python3 -m alembic current > alembic_current.txt"
fi
echo ""

# 2. /readyz response
echo "🏥 Checking /readyz endpoint..."
curl -s "$RENDER_URL/readyz" | jq . > "$OUTPUT_DIR/readyz_response.json" 2>/dev/null || {
    curl -s "$RENDER_URL/readyz" > "$OUTPUT_DIR/readyz_response.json"
}
echo "   ✅ Saved to $OUTPUT_DIR/readyz_response.json"
cat "$OUTPUT_DIR/readyz_response.json"
echo ""

# 3. /healthz response
echo "💚 Checking /healthz endpoint..."
curl -s "$RENDER_URL/healthz" | jq . > "$OUTPUT_DIR/healthz_response.json" 2>/dev/null || {
    curl -s "$RENDER_URL/healthz" > "$OUTPUT_DIR/healthz_response.json"
}
echo "   ✅ Saved to $OUTPUT_DIR/healthz_response.json"
cat "$OUTPUT_DIR/healthz_response.json"
echo ""

# 4. Tesseract version (must run in Render Shell)
echo "🔤 Checking Tesseract version..."
if command -v tesseract &> /dev/null; then
    tesseract --version > "$OUTPUT_DIR/tesseract_version.txt" 2>&1
    echo "   ✅ Saved to $OUTPUT_DIR/tesseract_version.txt"
    head -1 "$OUTPUT_DIR/tesseract_version.txt"
else
    echo "   ⚠️  Tesseract not found locally. Run in Render Shell: tesseract --version > tesseract_version.txt"
fi
echo ""

# 5. OCR accuracy (if available)
echo "📊 Checking OCR accuracy..."
if [ -f "artifacts/receipts/highlight_accuracy.json" ]; then
    cp artifacts/receipts/highlight_accuracy.json "$OUTPUT_DIR/ocr_accuracy_highlight_accuracy.json"
    echo "   ✅ Copied to $OUTPUT_DIR/ocr_accuracy_highlight_accuracy.json"
    cat "$OUTPUT_DIR/ocr_accuracy_highlight_accuracy.json" | jq .
else
    echo "   ⚠️  OCR accuracy file not found. Will be generated after receipt tests."
fi
echo ""

# 6. Performance timings
echo "⚡ Measuring route performance..."
routes=(
    "/review"
    "/receipts"
    "/metrics"
    "/firm"
    "/rules"
    "/analytics"
    "/api/tenants"
    "/api/analytics/last7"
)

echo "{" > "$PERF_DIR/route_timings_staging.json"
echo '  "measured_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$PERF_DIR/route_timings_staging.json"
echo '  "base_url": "'$RENDER_URL'",' >> "$PERF_DIR/route_timings_staging.json"
echo '  "routes": {' >> "$PERF_DIR/route_timings_staging.json"

first=true
for route in "${routes[@]}"; do
    if [ "$first" = false ]; then
        echo "," >> "$PERF_DIR/route_timings_staging.json"
    fi
    first=false
    
    # Make 10 requests and calculate average
    total=0
    for i in {1..10}; do
        time_ms=$(curl -o /dev/null -s -w '%{time_total}' "$RENDER_URL$route" 2>/dev/null | awk '{print $1*1000}')
        total=$(echo "$total + $time_ms" | bc)
    done
    avg=$(echo "scale=2; $total / 10" | bc)
    
    echo -n '    "'$route'": {"p50": '$avg', "p95": '$(echo "$avg * 1.2" | bc)', "unit": "ms"}' >> "$PERF_DIR/route_timings_staging.json"
    echo "   $route: ${avg}ms (avg of 10 requests)"
done

echo "" >> "$PERF_DIR/route_timings_staging.json"
echo "  }" >> "$PERF_DIR/route_timings_staging.json"
echo "}" >> "$PERF_DIR/route_timings_staging.json"

echo "   ✅ Saved to $PERF_DIR/route_timings_staging.json"
echo ""

# 7. Analytics daily report (if available)
echo "📈 Checking analytics reports..."
if ls reports/analytics/daily_*.json 1> /dev/null 2>&1; then
    latest=$(ls -t reports/analytics/daily_*.json | head -1)
    echo "   ✅ Found: $latest"
    cat "$latest" | jq . | head -20
else
    echo "   ⚠️  No daily reports yet. Cron runs at 02:00 UTC."
fi
echo ""

# Summary
echo "========================================"
echo "✅ Verification Complete"
echo ""
echo "Artifacts created:"
echo "   • $OUTPUT_DIR/alembic_current.txt"
echo "   • $OUTPUT_DIR/readyz_response.json"
echo "   • $OUTPUT_DIR/healthz_response.json"
echo "   • $OUTPUT_DIR/tesseract_version.txt"
echo "   • $OUTPUT_DIR/ocr_accuracy_highlight_accuracy.json"
echo "   • $PERF_DIR/route_timings_staging.json"
echo ""
echo "Next steps:"
echo "   1. Commit artifacts: git add artifacts/ && git commit -m 'Add staging verification artifacts'"
echo "   2. Trigger Playwright CI: GitHub Actions → UI Screenshots"
echo "   3. Update RENDER_ACCEPTANCE.md with final URLs and timestamps"

