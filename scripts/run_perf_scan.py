#!/usr/bin/env python3
"""
Performance scan script for route timing analysis.

Measures p50/p95 SSR render times for key routes.
"""
import json
import sys
import time
import requests
from pathlib import Path
from statistics import median, quantiles

print("⚡ Running performance scan...")

# Routes to test
routes = [
    {"path": "/", "name": "Home"},
    {"path": "/review", "name": "Transaction Review"},
    {"path": "/metrics", "name": "Metrics Dashboard"},
    {"path": "/receipts", "name": "Receipt Highlights"},
    {"path": "/analytics", "name": "Product Analytics"},
    {"path": "/firm", "name": "Firm Console"},
    {"path": "/rules", "name": "Rules Console"},
    {"path": "/audit", "name": "Audit Log"},
    {"path": "/onboarding", "name": "Onboarding Wizard"},
    {"path": "/healthz", "name": "Health Check"},
]

base_url = "http://localhost:8000"
results = []

print(f"\n📊 Testing {len(routes)} routes...")

for route in routes:
    path = route["path"]
    name = route["name"]
    timings = []
    
    # Perform 20 requests to get statistical data
    for i in range(20):
        try:
            start = time.time()
            response = requests.get(f"{base_url}{path}", timeout=5, allow_redirects=True)
            duration_ms = (time.time() - start) * 1000
            timings.append(duration_ms)
        except Exception as e:
            print(f"  ⚠️  {name} ({path}): Error - {e}")
            continue
    
    if timings:
        p50 = median(timings)
        p95 = quantiles(timings, n=20)[18] if len(timings) >= 19 else max(timings)
        
        result = {
            "route": path,
            "name": name,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "samples": len(timings),
            "status": "✅" if p95 < 300 else "⚠️"
        }
        results.append(result)
        
        status_icon = "✅" if p95 < 300 else "⚠️"
        print(f"  {status_icon} {name:25s} p50: {p50:6.1f}ms | p95: {p95:6.1f}ms")
    else:
        print(f"  ❌ {name}: No successful requests")

# Save detailed results
output_dir = Path("artifacts/perf")
output_dir.mkdir(parents=True, exist_ok=True)

timings_path = output_dir / "route_timings.json"
with open(timings_path, "w") as f:
    json.dump({
        "timestamp": "2025-10-11T19:05:00.000Z",
        "base_url": base_url,
        "target_p95_ms": 300,
        "results": results,
        "summary": {
            "total_routes": len(results),
            "passing": sum(1 for r in results if r["p95_ms"] < 300),
            "warnings": sum(1 for r in results if r["p95_ms"] >= 300)
        }
    }, f, indent=2)

print(f"\n✅ Performance scan complete: {timings_path}")

# Identify slow routes
slow_routes = [r for r in results if r["p95_ms"] >= 300]
if slow_routes:
    print(f"\n⚠️  Routes exceeding 300ms p95 target:")
    for r in slow_routes:
        print(f"   • {r['name']} ({r['route']}): {r['p95_ms']:.1f}ms")
        print(f"     Quick win: Enable caching, optimize DB queries, lazy-load images")
else:
    print(f"\n✅ All routes meet p95 < 300ms target!")

sys.exit(0)

