#!/bin/bash

# PSE Verification Script
# =======================
# Quick verification commands for PSE guide pages

set -e

BASE_URL="${NEXT_PUBLIC_SITE_URL:-https://ai-bookkeeper.app}"

echo "🧪 Verifying PSE Implementation..."
echo ""

# Active guide 200
echo "1️⃣ Active guide (Chase) should return 200:"
curl -sI "${BASE_URL}/guides/chase-export-csv" | head -5
echo ""

# Noindex guide 200 and robots tag
echo "2️⃣ Noindex guide (People's United) should return 200 with noindex:"
curl -s "${BASE_URL}/guides/peoples-united-export-csv" | grep -i 'name="robots"' || echo "⚠️ Robots meta tag not found in HTML"
echo ""

# Sitemap contains guides
echo "3️⃣ Sitemap should contain ≥50 guide URLs:"
GUIDE_COUNT=$(curl -s "${BASE_URL}/sitemap.xml" | grep -c '/guides/' || echo "0")
echo "Found: ${GUIDE_COUNT} guide URLs"
if [ "$GUIDE_COUNT" -ge 50 ]; then
  echo "✅ Pass: ${GUIDE_COUNT} ≥ 50"
else
  echo "❌ Fail: ${GUIDE_COUNT} < 50"
fi
echo ""

# OG endpoint 200
echo "4️⃣ OG image endpoint should return 200:"
curl -sI "${BASE_URL}/api/og/pse?slug=chase-export-csv" | head -5
echo ""

echo "✅ Verification complete!"

