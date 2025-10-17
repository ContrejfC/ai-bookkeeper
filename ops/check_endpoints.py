#!/usr/bin/env python3
"""
Endpoint health check script for AI Bookkeeper
Checks core endpoints and generates status reports
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class EndpointChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results = []
        
    def check_endpoint(self, path: str, method: str = "GET", expected_status: int = 200, 
                      description: str = "", requires_auth: bool = False) -> Dict[str, Any]:
        """Check a single endpoint and return results"""
        url = f"{self.base_url}{path}"
        start_time = datetime.now()
        
        try:
            response = requests.request(method, url, timeout=10)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            result = {
                "url": url,
                "method": method,
                "description": description,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "response_time_ms": round(response_time * 1000, 2),
                "success": response.status_code == expected_status,
                "requires_auth": requires_auth,
                "timestamp": start_time.isoformat(),
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content)
            }
            
            # Add error details if failed
            if not result["success"]:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
                if response.status_code >= 500:
                    result["error_detail"] = response.text[:500]  # Truncate error details
                    
        except requests.exceptions.RequestException as e:
            result = {
                "url": url,
                "method": method,
                "description": description,
                "expected_status": expected_status,
                "actual_status": None,
                "response_time_ms": None,
                "success": False,
                "requires_auth": requires_auth,
                "timestamp": start_time.isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
            
        self.results.append(result)
        return result
        
    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        print(f"Checking endpoints at {self.base_url}")
        
        # Core health endpoints
        self.check_endpoint("/healthz", description="Health check endpoint")
        self.check_endpoint("/readyz", description="Readiness check endpoint")
        
        # API documentation
        self.check_endpoint("/openapi.json", description="OpenAPI specification")
        self.check_endpoint("/docs", description="API documentation")
        
        # Authentication endpoints
        self.check_endpoint("/api/auth/login", method="POST", expected_status=422, 
                           description="Login endpoint (expect validation error without data)")
        self.check_endpoint("/api/auth/signup", method="POST", expected_status=422,
                           description="Signup endpoint (expect validation error without data)")
        
        # Protected endpoints (should require auth)
        self.check_endpoint("/api/dashboard", expected_status=401, 
                           description="Dashboard (protected)", requires_auth=True)
        self.check_endpoint("/api/transactions", expected_status=401,
                           description="Transactions (protected)", requires_auth=True)
        
        # UI endpoints
        self.check_endpoint("/", description="Home page")
        self.check_endpoint("/legal/terms", description="Terms page")
        self.check_endpoint("/legal/privacy", description="Privacy page")
        
        return self.generate_summary()
        
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all checks"""
        total_checks = len(self.results)
        successful_checks = sum(1 for r in self.results if r["success"])
        failed_checks = total_checks - successful_checks
        
        # Group by status
        status_groups = {}
        for result in self.results:
            status = result["actual_status"] if result["actual_status"] is not None else "ERROR"
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)
            
        # Performance metrics
        response_times = [r["response_time_ms"] for r in self.results if r["response_time_ms"] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "success_rate": round((successful_checks / total_checks) * 100, 2) if total_checks > 0 else 0,
            "average_response_time_ms": round(avg_response_time, 2),
            "status_groups": status_groups,
            "results": self.results
        }
        
        return summary

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    checker = EndpointChecker(base_url)
    summary = checker.run_health_checks()
    
    # Print summary to console
    print(f"\n=== ENDPOINT HEALTH CHECK SUMMARY ===")
    print(f"Base URL: {summary['base_url']}")
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Successful: {summary['successful_checks']}")
    print(f"Failed: {summary['failed_checks']}")
    print(f"Success Rate: {summary['success_rate']}%")
    print(f"Average Response Time: {summary['average_response_time_ms']}ms")
    
    # Print failed checks
    if summary['failed_checks'] > 0:
        print(f"\n=== FAILED CHECKS ===")
        for result in summary['results']:
            if not result['success']:
                print(f"❌ {result['method']} {result['url']} - {result.get('error', 'Unknown error')}")
    
    # Save detailed results
    os.makedirs("reports", exist_ok=True)
    with open("reports/endpoint_status.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nDetailed results saved to reports/endpoint_status.json")
    
    # Return exit code based on success rate
    if summary['success_rate'] >= 80:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
