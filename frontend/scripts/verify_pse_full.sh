#!/bin/bash
# PSE Full Verification Script
# 6 checks as specified

set -e

BASE="${NEXT_PUBLIC_SITE_URL:-https://ai-bookkeeper.app}"

echo "🧪 PSE Verification (6 checks)"
echo ""

# 1) Active guide returns 200
echo "1️⃣ Active guide HTTP status:"
curl -sI ${BASE}/guides/chase-export-csv | head -1
echo ""

# 2) Count JSON-LD blocks (should be ≥2)
echo "2️⃣ JSON-LD block count:"
curl -s ${BASE}/guides/chase-export-csv | grep -c 'application/ld+json'
echo ""

# 3) Noindex page has robots meta
echo "3️⃣ Noindex robots meta:"
curl -s ${BASE}/guides/peoples-united-export-csv | grep -i 'name="robots"'
echo ""

# 4) Sitemap guide count (should be ≥50)
echo "4️⃣ Sitemap guide URLs:"
curl -s ${BASE}/sitemap.xml | grep -c '/guides/'
echo ""

# 5) Noindex absent from sitemap (should be 0)
echo "5️⃣ Noindex in sitemap (should be 0):"
curl -s ${BASE}/sitemap.xml | grep -c '/guides/peoples-united'
echo ""

# 6) OG endpoint
echo "6️⃣ OG endpoint headers:"
curl -sI "${BASE}/api/og/pse?slug=chase-export-csv" | grep -Ei 'HTTP/|content-type|cache-control'
echo ""

echo "✅ All 6 checks complete"

