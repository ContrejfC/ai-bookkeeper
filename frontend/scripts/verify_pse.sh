#!/bin/bash
# PSE Verification Script
# Clean zsh-safe commands

set -e

BASE="https://ai-bookkeeper.app"

echo "🧪 PSE Verification"
echo ""

# 1) Active guide returns 200
echo "1️⃣ Active guide (chase-export-csv):"
curl -sI ${BASE}/guides/chase-export-csv | head -5
echo ""

# 2) Count JSON-LD blocks on the page
echo "2️⃣ JSON-LD count (should be ≥2):"
COUNT=$(curl -s ${BASE}/guides/chase-export-csv | grep -c 'application/ld+json' || echo 0)
echo "Found: $COUNT"
echo ""

# 3) Noindex page has robots meta
echo "3️⃣ Noindex page robots meta:"
curl -s ${BASE}/guides/peoples-united-export-csv | grep -i 'name="robots"' || echo "⚠️ Not found"
echo ""

# 4) Noindex page absent from sitemap
echo "4️⃣ Noindex page NOT in sitemap (should be 0):"
COUNT=$(curl -s ${BASE}/sitemap.xml | grep -c '/guides/peoples-united' || echo 0)
echo "Count: $COUNT"
echo ""

# 5) Sitemap has many guides
echo "5️⃣ Sitemap guide count (should be ≥50):"
COUNT=$(curl -s ${BASE}/sitemap.xml | grep -c '/guides/' || echo 0)
echo "Found: $COUNT guide URLs"
echo ""

# 6) OG endpoint works and is cacheable
echo "6️⃣ OG endpoint:"
curl -sI "${BASE}/api/og/pse?slug=chase-export-csv" | grep -Ei 'HTTP/|content-type|cache-control'
echo ""

echo "✅ Verification complete"
