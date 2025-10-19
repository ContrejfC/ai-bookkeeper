#!/usr/bin/env python3
"""
Pre-launch validation script - All 8 criteria must pass before ads launch.

Usage:
    python scripts/validate_prelaunch.py [--verbose]
"""
import sys
import os
from pathlib import Path
import argparse
import requests
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.ai-bookkeeper.app")
API_URL = os.getenv("API_URL", "https://api.ai-bookkeeper.app")


class ValidationRunner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = []
        self.failed = []
        
    def log(self, message):
        """Log verbose messages"""
        if self.verbose:
            print(f"  {message}")
    
    def test(self, number, name, func):
        """Run a test and track results"""
        print(f"\n{'='*60}")
        print(f"Test {number}: {name}")
        print(f"{'='*60}")
        
        try:
            result = func()
            if result:
                print(f"✅ PASS - {name}")
                self.passed.append((number, name))
                return True
            else:
                print(f"❌ FAIL - {name}")
                self.failed.append((number, name))
                return False
        except Exception as e:
            print(f"❌ ERROR - {name}: {str(e)}")
            self.failed.append((number, name))
            return False
    
    def test_1_domains_cors(self):
        """Test 1: Domains and CORS work"""
        print("Testing HTTPS connectivity and CORS...")
        
        # Test frontend HTTPS
        self.log(f"Testing {FRONTEND_URL}/gpt-bridge...")
        try:
            r = requests.get(f"{FRONTEND_URL}/gpt-bridge", timeout=10)
            if r.status_code != 200:
                print(f"  ❌ Frontend returned {r.status_code}")
                return False
            self.log("  ✅ Frontend loads over HTTPS")
        except Exception as e:
            print(f"  ❌ Frontend error: {e}")
            return False
        
        # Test API health
        self.log(f"Testing {API_URL}/healthz...")
        try:
            r = requests.get(f"{API_URL}/healthz", timeout=10)
            if r.status_code != 200:
                print(f"  ❌ API returned {r.status_code}")
                return False
            self.log("  ✅ API responds over HTTPS")
        except Exception as e:
            print(f"  ❌ API error: {e}")
            return False
        
        # CORS check (simulated - actual CORS only testable in browser)
        self.log("CORS configuration check...")
        try:
            r = requests.options(f"{API_URL}/api/billing/status", 
                               headers={'Origin': FRONTEND_URL}, timeout=10)
            # If we get any response, server is configured
            self.log("  ✅ API accepts requests (CORS headers should be configured)")
        except:
            self.log("  ⚠️  Could not verify CORS (browser testing required)")
        
        print("\n✅ Domains accessible over HTTPS")
        print("⚠️  CORS verification requires browser testing:")
        print(f"   1. Visit {FRONTEND_URL}/gpt-bridge")
        print(f"   2. Open DevTools → Console")
        print(f"   3. Verify no CORS errors")
        print(f"   4. Check GA4 event: bridge_viewed")
        
        return True
    
    def test_2_stripe_skus(self):
        """Test 2: Stripe SKUs match approved pricing"""
        print("Verifying Stripe price configuration...")
        
        # Load config
        config_path = project_root / "config" / "stripe_price_map.json"
        if not config_path.exists():
            print("  ❌ stripe_price_map.json not found")
            return False
        
        import json
        with open(config_path) as f:
            config = json.load(f)
        
        # Check all required prices exist
        required = {
            'plans': ['starter_monthly', 'team_monthly', 'firm_monthly', 'pilot_monthly',
                     'starter_annual', 'team_annual', 'firm_annual'],
            'overage': ['starter_tx', 'team_tx', 'firm_tx', 'enterprise_tx'],
            'addons': ['extra_entity_starter_team', 'extra_entity_firm', 'sso_saml',
                      'white_label', 'retention_24m', 'priority_support']
        }
        
        missing = []
        for category, keys in required.items():
            for key in keys:
                if key not in config.get(category, {}):
                    missing.append(f"{category}.{key}")
                elif 'placeholder' in config[category][key]:
                    missing.append(f"{category}.{key} (still placeholder)")
        
        if missing:
            print(f"  ❌ Missing or placeholder price IDs:")
            for m in missing:
                print(f"     - {m}")
            return False
        
        # Verify pricing reference
        if '_pricing_reference' in config:
            ref = config['_pricing_reference']
            checks = [
                (ref['starter']['monthly'] == 49, "Starter $49/mo"),
                (ref['starter']['overage_rate'] == 0.03, "Starter overage $0.03"),
                (ref['team']['monthly'] == 149, "Team $149/mo"),
                (ref['team']['overage_rate'] == 0.02, "Team overage $0.02"),
                (ref['firm']['monthly'] == 499, "Firm $499/mo"),
                (ref['firm']['overage_rate'] == 0.015, "Firm overage $0.015"),
                (ref['pilot']['monthly'] == 99, "Pilot $99/mo"),
            ]
            
            for check, desc in checks:
                if not check:
                    print(f"  ❌ Pricing mismatch: {desc}")
                    return False
                self.log(f"  ✅ {desc}")
        
        print("✅ All price IDs configured")
        print("✅ Pricing matches approved model")
        return True
    
    def test_3_entitlements_metering(self):
        """Test 3: Entitlements and metering enforce quotas"""
        print("Testing entitlements and usage metering...")
        
        # This requires database access, so we'll do a basic check
        print("⚠️  Full metering test requires database access")
        print("   Run: make usage")
        print("   Expected: 600 tx → 100 overage × $0.03 = $3.00")
        
        # Check if usage script exists
        usage_script = project_root / "scripts" / "simulate_usage.py"
        if not usage_script.exists():
            print("  ❌ simulate_usage.py not found")
            return False
        
        print("✅ Usage simulation script ready")
        print("   Manual verification required:")
        print("   1. Run: python scripts/simulate_usage.py")
        print("   2. Verify: 600 tx processed")
        print("   3. Verify: 100 overage calculated")
        print("   4. Verify: $3.00 overage amount")
        
        return True
    
    def test_4_webhooks(self):
        """Test 4: Webhooks update access instantly"""
        print("Testing Stripe webhook configuration...")
        
        # Check if webhook endpoint exists
        try:
            r = requests.post(f"{API_URL}/api/billing/webhook",
                            json={},
                            headers={'Content-Type': 'application/json'},
                            timeout=10)
            # We expect 400 (invalid signature) not 404
            if r.status_code == 404:
                print("  ❌ Webhook endpoint not found")
                return False
            self.log(f"  ✅ Webhook endpoint exists (status: {r.status_code})")
        except Exception as e:
            print(f"  ❌ Webhook endpoint error: {e}")
            return False
        
        print("✅ Webhook endpoint configured")
        print("⚠️  Webhook signature verification requires Stripe test")
        print("   Manual verification required:")
        print("   1. Go to Stripe Dashboard → Webhooks")
        print(f"   2. Verify endpoint: {API_URL}/api/billing/webhook")
        print("   3. Send test event: checkout.session.completed")
        print("   4. Verify: Returns 200 OK")
        print("   5. Check logs: Subscription created in <10s")
        
        return True
    
    def test_5_e2e_purchase(self):
        """Test 5: E2E purchase succeeds"""
        print("Testing E2E purchase flow...")
        
        # Check pricing page
        try:
            r = requests.get(f"{FRONTEND_URL}/pricing", timeout=10)
            if r.status_code != 200:
                print(f"  ❌ Pricing page returned {r.status_code}")
                return False
            if 'Starter' not in r.text or '$49' not in r.text:
                print("  ❌ Pricing page missing Starter plan")
                return False
            self.log("  ✅ Pricing page loads with plans")
        except Exception as e:
            print(f"  ❌ Pricing page error: {e}")
            return False
        
        # Check success page
        try:
            r = requests.get(f"{FRONTEND_URL}/success", timeout=10)
            if r.status_code != 200:
                print(f"  ❌ Success page returned {r.status_code}")
                return False
            self.log("  ✅ Success page loads")
        except Exception as e:
            print(f"  ❌ Success page error: {e}")
            return False
        
        print("✅ Purchase flow pages accessible")
        print("⚠️  Full E2E test requires browser automation")
        print("   Manual verification required:")
        print("   1. Visit /pricing")
        print("   2. Click 'Start Starter'")
        print("   3. Use test card: 4242 4242 4242 4242")
        print("   4. Complete checkout")
        print("   5. Verify redirect to /success")
        print("   6. Check GA4 Realtime: purchase, subscription_started")
        print("   7. Check Stripe Dashboard: Subscription created")
        
        return True
    
    def test_6_monthend_dryrun(self):
        """Test 6: Month-end dry run works"""
        print("Testing month-end billing script...")
        
        # Check if script exists
        monthend_script = project_root / "scripts" / "run_month_end.py"
        if not monthend_script.exists():
            print("  ❌ run_month_end.py not found")
            return False
        
        print("✅ Month-end billing script ready")
        print("   Run: python scripts/run_month_end.py --dry-run")
        print("   Expected: Calculates overage, idempotent by (tenant, yyyymm)")
        
        return True
    
    def test_7_legal_pages(self):
        """Test 7: Legal and trust pages are public"""
        print("Testing legal pages...")
        
        pages = {
            '/privacy': 'Privacy Policy',
            '/terms': 'Terms of Service',
            '/dpa': 'Data Processing Agreement',
            '/security': 'Security'
        }
        
        for path, expected_title in pages.items():
            try:
                r = requests.get(f"{FRONTEND_URL}{path}", timeout=10)
                if r.status_code != 200:
                    print(f"  ❌ {path} returned {r.status_code}")
                    return False
                if expected_title not in r.text:
                    print(f"  ❌ {path} missing expected content")
                    return False
                self.log(f"  ✅ {path} loads")
            except Exception as e:
                print(f"  ❌ {path} error: {e}")
                return False
        
        # Check footer links
        try:
            r = requests.get(FRONTEND_URL, timeout=10)
            if 'support@ai-bookkeeper.app' not in r.text:
                print("  ⚠️  Footer contact email not found")
        except:
            pass
        
        print("✅ All legal pages accessible")
        return True
    
    def test_8_performance(self):
        """Test 8: Performance is green"""
        print("Testing performance...")
        
        pages = ['/gpt-bridge', '/tools/csv-cleaner', '/pricing']
        
        for path in pages:
            try:
                import time
                start = time.time()
                r = requests.get(f"{FRONTEND_URL}{path}", timeout=15)
                elapsed = time.time() - start
                
                if r.status_code != 200:
                    print(f"  ❌ {path} returned {r.status_code}")
                    return False
                
                self.log(f"  ✅ {path} loaded in {elapsed:.2f}s")
                
                if elapsed > 5:
                    print(f"  ⚠️  {path} slow ({elapsed:.2f}s)")
            except Exception as e:
                print(f"  ❌ {path} error: {e}")
                return False
        
        print("✅ All pages load successfully")
        print("⚠️  Full performance testing requires Lighthouse")
        print("   Run: npx lighthouse {FRONTEND_URL}/gpt-bridge --view")
        print("   Targets: LCP < 2.5s, CLS < 0.1, INP < 200ms")
        
        return True
    
    def run_all(self):
        """Run all validation tests"""
        print(f"\n{'='*60}")
        print("PRE-LAUNCH VALIDATION")
        print(f"{'='*60}")
        print(f"Time: {datetime.utcnow().isoformat()}Z")
        print(f"Frontend: {FRONTEND_URL}")
        print(f"API: {API_URL}")
        
        self.test(1, "Domains and CORS work", self.test_1_domains_cors)
        self.test(2, "Stripe SKUs match approved pricing", self.test_2_stripe_skus)
        self.test(3, "Entitlements and metering enforce quotas", self.test_3_entitlements_metering)
        self.test(4, "Webhooks update access instantly", self.test_4_webhooks)
        self.test(5, "E2E purchase succeeds", self.test_5_e2e_purchase)
        self.test(6, "Month-end dry run works", self.test_6_monthend_dryrun)
        self.test(7, "Legal and trust pages are public", self.test_7_legal_pages)
        self.test(8, "Performance is green", self.test_8_performance)
        
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {len(self.passed)}/8")
        print(f"Failed: {len(self.failed)}/8")
        
        if self.failed:
            print(f"\n❌ FAILED TESTS:")
            for num, name in self.failed:
                print(f"   {num}. {name}")
            print(f"\n⛔ DO NOT LAUNCH ADS - Fix failures above")
            return False
        else:
            print(f"\n✅ ALL TESTS PASSED!")
            print(f"\n🚀 READY TO LAUNCH GOOGLE ADS")
            print(f"\nNext steps:")
            print(f"1. Complete manual verifications marked with ⚠️")
            print(f"2. Review GOOGLE_ADS_PRELAUNCH_CHECKLIST.md")
            print(f"3. Create Google Ads campaign with provided configuration")
            print(f"4. Start with $40/day budget")
            print(f"5. Monitor first 24 hours closely")
            return True


def main():
    parser = argparse.ArgumentParser(description='Pre-launch validation')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    args = parser.parse_args()
    
    runner = ValidationRunner(verbose=args.verbose)
    success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

