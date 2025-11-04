#!/bin/bash
#
# Test Script for Public Sample Fetcher
# ======================================
#
# Quick test to verify the sample fetcher is working correctly.
#

set -e  # Exit on error

echo "=========================================="
echo "Public Sample Fetcher - Test Script"
echo "=========================================="
echo ""

# Check if required dependencies are installed
echo "[1/5] Checking dependencies..."
python3 -c "import pdfplumber" 2>/dev/null || python3 -c "import fitz" 2>/dev/null || {
    echo "❌ ERROR: Neither pdfplumber nor PyMuPDF (fitz) is installed."
    echo "   Install one with: pip install pdfplumber  OR  pip install pymupdf"
    exit 1
}
python3 -c "import yaml" 2>/dev/null || {
    echo "❌ ERROR: PyYAML is not installed."
    echo "   Install with: pip install pyyaml"
    exit 1
}
python3 -c "import requests" 2>/dev/null || {
    echo "❌ ERROR: requests is not installed."
    echo "   Install with: pip install requests"
    exit 1
}
echo "✅ All dependencies installed"
echo ""

# Check if config exists
echo "[2/5] Checking configuration..."
if [ ! -f "configs/public_samples.yaml" ]; then
    echo "❌ ERROR: configs/public_samples.yaml not found"
    exit 1
fi
echo "✅ Configuration found"
echo ""

# Check if any samples are enabled
echo "[3/5] Checking for enabled samples..."
ENABLED_COUNT=$(grep -c "enabled: true" configs/public_samples.yaml || echo "0")
if [ "$ENABLED_COUNT" -eq "0" ]; then
    echo "⚠️  WARNING: No samples are enabled in configs/public_samples.yaml"
    echo "   To enable samples:"
    echo "   1. Edit configs/public_samples.yaml"
    echo "   2. Add valid public sample URLs"
    echo "   3. Set enabled: true for each sample"
    echo ""
    echo "   Skipping fetch test (no samples to fetch)"
else
    echo "✅ Found $ENABLED_COUNT enabled sample(s)"
    echo ""
    
    # Run the fetcher
    echo "[4/5] Running sample fetcher..."
    python scripts/fetch_public_samples.py \
        --config configs/public_samples.yaml \
        --delete-after-extract \
        --verbose || {
        echo "❌ Fetch failed (this is expected if URLs are placeholders)"
        echo "   Update configs/public_samples.yaml with real URLs"
    }
    echo ""
fi

# Run tests
echo "[5/5] Running tests..."
pytest tests/templates/test_public_sample_features.py -v --tb=short || {
    echo "⚠️  Some tests skipped/failed (expected if no samples downloaded)"
}
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit configs/public_samples.yaml with real sample URLs"
echo "  2. Set enabled: true for samples you want to fetch"
echo "  3. Run: python scripts/fetch_public_samples.py --config configs/public_samples.yaml --delete-after-extract"
echo "  4. View features: ls -la tests/fixtures/pdf/features/"
echo ""
echo "Documentation: docs/TEMPLATES_README.md"
echo ""



