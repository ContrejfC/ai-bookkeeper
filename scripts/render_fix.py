#!/usr/bin/env python3
"""
Render Drift Detection and Fix Script
Identifies services that don't match render.yaml configuration and provides cleanup commands.
"""

import os
import json
import requests
import sys
import yaml
from typing import Dict, List, Any

BASE = "https://api.render.com/v1"

def get_services(api_key: str) -> List[Dict]:
    """Fetch all services from Render API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(f"{BASE}/services", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching services: {e}")
        return []

def load_render_yaml() -> Dict[str, Any]:
    """Load and parse render.yaml configuration."""
    try:
        with open("render.yaml", "r") as f:
            config = yaml.safe_load(f)
        return {s["name"]: s for s in config["services"]}
    except FileNotFoundError:
        print("❌ Error: render.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing render.yaml: {e}")
        sys.exit(1)

def analyze_drift(desired: Dict[str, Any], live: List[Dict]) -> Dict[str, Any]:
    """Analyze drift between desired and live services."""
    keep = set(desired.keys())
    live_names = [s["name"] for s in live]
    stray = [s for s in live if s["name"] not in keep]
    
    return {
        "desired": list(keep),
        "live": live_names,
        "stray": [s["name"] for s in stray],
        "stray_details": stray,
        "missing": [name for name in keep if name not in live_names]
    }

def print_drift_report(analysis: Dict[str, Any]):
    """Print human-readable drift report."""
    print("\n" + "="*80)
    print("RENDER DRIFT ANALYSIS")
    print("="*80)
    
    print(f"Desired services: {', '.join(sorted(analysis['desired']))}")
    print(f"Live services:    {', '.join(sorted(analysis['live']))}")
    
    if analysis["stray"]:
        print(f"\n🚨 STRAY SERVICES DETECTED ({len(analysis['stray'])}):")
        print("-" * 50)
        for service in analysis["stray_details"]:
            print(f"• {service['name']}")
            print(f"  ID: {service['id']}")
            print(f"  Type: {service['type']}")
            print(f"  Env: {service.get('env', 'unknown')}")
            print(f"  URL: {service.get('url', 'N/A')}")
            print(f"  Delete: curl -H 'Authorization: Bearer $RENDER_API_KEY' -X DELETE {BASE}/services/{service['id']}")
            print()
    else:
        print("\n✅ No stray services detected")
    
    if analysis["missing"]:
        print(f"\n⚠️  MISSING SERVICES ({len(analysis['missing'])}):")
        print("-" * 50)
        for service_name in analysis["missing"]:
            print(f"• {service_name}")
        print("\nThese will be created when you apply the Blueprint.")
    else:
        print("\n✅ All desired services are present")

def save_drift_report(analysis: Dict[str, Any], filename: str = "tmp/render_drift.json"):
    """Save drift analysis to JSON file."""
    os.makedirs("tmp", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\n💾 Drift report saved to {filename}")

def main():
    """Main execution function."""
    # Check for API key
    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("Usage: export RENDER_API_KEY=your_key && python3 scripts/render_fix.py")
        sys.exit(1)
    
    print("🔍 Analyzing Render service drift...")
    
    # Load desired configuration
    desired = load_render_yaml()
    print(f"✅ Loaded render.yaml with {len(desired)} desired services")
    
    # Fetch live services
    live = get_services(api_key)
    if not live:
        print("❌ No services found or API error")
        sys.exit(1)
    
    print(f"✅ Found {len(live)} live services")
    
    # Analyze drift
    analysis = analyze_drift(desired, live)
    
    # Print report
    print_drift_report(analysis)
    
    # Save report
    save_drift_report(analysis)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    if analysis["stray"]:
        print(f"❌ {len(analysis['stray'])} stray services need deletion")
        print("📋 Next steps:")
        print("1. Delete stray services using the curl commands above")
        print("2. Apply Blueprint: Render Dashboard → New → Blueprint")
        print("3. Connect repository and apply render.yaml")
    else:
        print("✅ No cleanup needed")
        print("📋 Next steps:")
        print("1. Apply Blueprint: Render Dashboard → New → Blueprint")
        print("2. Connect repository and apply render.yaml")
    
    print("\n🎯 Expected result: Only ai-bookkeeper-api and ai-bookkeeper-web services")

if __name__ == "__main__":
    main()
