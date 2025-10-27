#!/usr/bin/env python3
"""
Render Deployment Status Audit Script
Queries Render API v1 to collect authoritative service status and deployment history.
"""

import os
import json
import sys
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

class RenderAuditor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        self.services = []
        self.deployments = {}
        
    def fetch_services(self) -> List[Dict]:
        """Fetch all services from Render API."""
        try:
            response = requests.get(f"{self.base_url}/services", headers=self.headers)
            response.raise_for_status()
            self.services = response.json()
            return self.services
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching services: {e}")
            return []
    
    def fetch_service_deployments(self, service_id: str, limit: int = 3) -> List[Dict]:
        """Fetch recent deployments for a service."""
        try:
            response = requests.get(
                f"{self.base_url}/services/{service_id}/deploys",
                headers=self.headers,
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching deployments for {service_id}: {e}")
            return []
    
    def fetch_deploy_logs(self, service_id: str, deploy_id: str) -> Optional[str]:
        """Fetch logs for a specific deployment."""
        try:
            response = requests.get(
                f"{self.base_url}/services/{service_id}/deploys/{deploy_id}/logs",
                headers=self.headers
            )
            response.raise_for_status()
            logs = response.text
            # Return last 50 lines
            lines = logs.split('\n')
            return '\n'.join(lines[-50:]) if len(lines) > 50 else logs
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching logs for deploy {deploy_id}: {e}")
            return None
    
    def analyze_services(self) -> Dict[str, Any]:
        """Analyze all services and their deployment status."""
        if not self.services:
            return {}
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(self.services),
            "services": {}
        }
        
        for service in self.services:
            service_id = service["id"]
            service_name = service["name"]
            
            # Fetch recent deployments
            deployments = self.fetch_service_deployments(service_id)
            
            # Analyze latest deployment
            latest_deploy = deployments[0] if deployments else None
            latest_logs = None
            
            if latest_deploy and latest_deploy.get("status") == "build_failed":
                latest_logs = self.fetch_deploy_logs(service_id, latest_deploy["id"])
            
            analysis["services"][service_name] = {
                "id": service_id,
                "type": service.get("type"),
                "env": service.get("env"),
                "rootDir": service.get("rootDir"),
                "buildCommand": service.get("buildCommand"),
                "startCommand": service.get("startCommand"),
                "url": service.get("url"),
                "updatedAt": service.get("updatedAt"),
                "deployments": deployments,
                "latest_logs": latest_logs
            }
        
        return analysis
    
    def print_status_table(self, analysis: Dict[str, Any]):
        """Print a human-readable status table."""
        print("\n" + "="*120)
        print("RENDER DEPLOYMENT STATUS AUDIT")
        print("="*120)
        print(f"Timestamp: {analysis['timestamp']}")
        print(f"Total Services: {analysis['total_services']}")
        print("\n" + "-"*120)
        print(f"{'Service Name':<25} {'Type':<8} {'Env':<8} {'Status':<12} {'Last Deploy':<20} {'URL':<40}")
        print("-"*120)
        
        for service_name, service_data in analysis["services"].items():
            latest_deploy = service_data["deployments"][0] if service_data["deployments"] else None
            status = latest_deploy["status"] if latest_deploy else "unknown"
            last_deploy = latest_deploy["createdAt"][:19] if latest_deploy else "never"
            url = service_data["url"] or "N/A"
            
            # Status emoji
            status_emoji = {
                "live": "✅",
                "build_failed": "❌",
                "build_in_progress": "🟡",
                "deploy_failed": "❌",
                "deploy_in_progress": "🟡",
                "unknown": "❓"
            }.get(status, "❓")
            
            print(f"{service_name:<25} {service_data['type']:<8} {service_data['env']:<8} "
                  f"{status_emoji} {status:<10} {last_deploy:<20} {url:<40}")
        
        print("-"*120)
    
    def save_json(self, analysis: Dict[str, Any], filename: str = "tmp/render_state.json"):
        """Save analysis to JSON file."""
        os.makedirs("tmp", exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Analysis saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Render Deployment Status Audit")
    parser.add_argument("--api-key", help="Render API key (or set RENDER_API_KEY env var)")
    parser.add_argument("--output", default="tmp/render_state.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("RENDER_API_KEY")
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("Usage: export RENDER_API_KEY=your_key && python3 scripts/render_status.py")
        sys.exit(1)
    
    # Run audit
    auditor = RenderAuditor(api_key)
    
    print("🔍 Fetching services from Render API...")
    services = auditor.fetch_services()
    
    if not services:
        print("❌ No services found or API error")
        sys.exit(1)
    
    print(f"✅ Found {len(services)} services")
    
    print("🔍 Analyzing deployments...")
    analysis = auditor.analyze_services()
    
    auditor.print_status_table(analysis)
    auditor.save_json(analysis, args.output)
    
    print("\n✅ Audit complete!")

if __name__ == "__main__":
    main()

