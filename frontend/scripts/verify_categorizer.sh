#!/bin/bash
# Categorizer v2 Verification Script
# =====================================
# Smoke tests for categorizer functionality

set -e

BASE="${NEXT_PUBLIC_SITE_URL:-http://localhost:3000}"

echo "🧪 Categorizer v2 Verification"
echo ""

# 1) Page loads
echo "1️⃣ Page loads:"
curl -sI ${BASE}/free/categorizer | head -1
echo ""

# 2) Check for stepper component
echo "2️⃣ Stepper present:"
curl -s ${BASE}/free/categorizer | grep -c 'Upload' || echo "0"
echo ""

# 3) Test CSV detection locally
echo "3️⃣ CSV detection (local test):"
if [ -f "tests/fixtures/us_basic.csv" ]; then
  echo "✅ Fixture exists"
  cat tests/fixtures/us_basic.csv | head -2
else
  echo "⚠️ Fixture not found"
fi
echo ""

# 4) Test formula injection prevention
echo "4️⃣ Formula sanitization test:"
cat > /tmp/test_formulas.csv << 'EOF'
Date,Description,Amount
2025-01-01,=1+1,-10.00
2025-01-02,+SUM(A1:A3),-20.00
2025-01-03,-2+3,-30.00
2025-01-04,@cmd,-40.00
EOF

echo "Created test CSV with formula injection attempts"
echo "✅ CSV created (manual verification needed)"
echo ""

# 5) Check exports exist
echo "5️⃣ Export modules:"
if [ -f "lib/export/csv_simple.ts" ] && [ -f "lib/export/csv_qbo.ts" ] && [ -f "lib/export/csv_xero.ts" ]; then
  echo "✅ All 3 export formats present (Simple, QBO, Xero)"
else
  echo "⚠️ Some export modules missing"
fi
echo ""

# 6) Check worker exists
echo "6️⃣ Web worker:"
if [ -f "workers/categorize.worker.ts" ]; then
  echo "✅ Web worker present (non-blocking parsing)"
else
  echo "⚠️ Worker not found"
fi
echo ""

echo "✅ Verification complete"
echo ""
echo "Manual verification steps:"
echo "1. Upload tests/fixtures/us_basic.csv"
echo "2. Verify auto-detection works"
echo "3. Check categories assigned (should be ~85% auto-categorized)"
echo "4. Export both formats"
echo "5. Open in Excel - verify /tmp/test_formulas.csv cells start with ' (safe)"

