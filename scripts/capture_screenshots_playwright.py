#!/usr/bin/env python3
"""
Automated UI Screenshot Capture using Playwright (Python).

Reads screenshot_manifest.json, logs in as demo owner, navigates to each
route, and captures full-page screenshots. Respects UI_ASSESSMENT=1 banner.

Usage:
    python scripts/capture_screenshots_playwright.py \\
        --base-url http://localhost:8000 \\
        --manifest artifacts/ui-assessment/screenshot_manifest.json \\
        --out artifacts/ui-assessment
"""
import json
import argparse
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def main():
    parser = argparse.ArgumentParser(description="Capture UI screenshots with Playwright")
    parser.add_argument("--base-url", required=True, help="Base URL of the application")
    parser.add_argument("--manifest", required=True, help="Path to screenshot_manifest.json")
    parser.add_argument("--out", required=True, help="Output directory for screenshots")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--user", default="owner@pilot-smb-001.demo", help="Login email")
    parser.add_argument("--password", default="demo-password-123", help="Login password")
    parser.add_argument("--timeout", type=int, default=30000, help="Page load timeout (ms)")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.out, exist_ok=True)
    
    # Load manifest
    try:
        with open(args.manifest, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"❌ Manifest not found: {args.manifest}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest: {e}")
        sys.exit(1)
    
    screens = manifest.get("screens", [])
    if not screens:
        print("⚠️  No screens defined in manifest")
        sys.exit(0)
    
    print(f"📸 Capturing {len(screens)} screenshots")
    print(f"   Base URL: {args.base_url}")
    print(f"   Output: {args.out}")
    print(f"   Headless: {args.headless}")
    print("")
    
    captured = 0
    failed = 0
    
    with sync_playwright() as pw:
        # Launch browser
        browser = pw.chromium.launch(headless=args.headless)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(args.timeout)
        
        try:
            # Step 1: Login
            print("🔐 Logging in...")
            login_success = login(page, args.base_url, args.user, args.password)
            
            if not login_success:
                print("❌ Login failed, aborting screenshot capture")
                browser.close()
                sys.exit(1)
            
            print("✅ Login successful")
            print("")
            
            # Step 2: Capture each screenshot
            for item in screens:
                path = item.get("path", "")
                filename = item.get("file", "")
                description = item.get("description", "")
                
                if not path or not filename:
                    print(f"⚠️  Skipping invalid manifest entry: {item}")
                    continue
                
                url = f"{args.base_url}{path}"
                out_path = os.path.join(args.out, filename)
                
                print(f"📸 {filename}")
                print(f"   URL: {url}")
                print(f"   Description: {description}")
                
                try:
                    # Navigate to URL
                    page.goto(url, wait_until="networkidle", timeout=args.timeout)
                    
                    # Wait a bit for any dynamic content
                    page.wait_for_timeout(1000)
                    
                    # Take screenshot
                    page.screenshot(path=out_path, full_page=True)
                    
                    print(f"   ✅ Saved to {out_path}")
                    captured += 1
                
                except PlaywrightTimeoutError:
                    print(f"   ⚠️  Timeout loading {url}")
                    failed += 1
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    failed += 1
                
                print("")
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        
        finally:
            browser.close()
    
    # Summary
    print("=" * 60)
    print(f"📊 Summary")
    print(f"   Total: {len(screens)}")
    print(f"   Captured: {captured}")
    print(f"   Failed: {failed}")
    print("=" * 60)
    
    # Exit with error if any failed
    if failed > 0:
        sys.exit(1)


def login(page, base_url, email, password):
    """
    Log in to the application.
    
    Returns True if successful, False otherwise.
    """
    try:
        # Navigate to login page
        login_url = f"{base_url}/login"
        page.goto(login_url, wait_until="networkidle")
        
        # Check if already logged in (redirected to /review)
        if "/review" in page.url:
            return True
        
        # Fill login form
        # Try multiple selector strategies
        try:
            page.fill('input[name="email"]', email)
        except:
            try:
                page.fill('input[type="email"]', email)
            except:
                page.fill('#email', email)
        
        try:
            page.fill('input[name="password"]', password)
        except:
            try:
                page.fill('input[type="password"]', password)
            except:
                page.fill('#password', password)
        
        # Click submit button
        try:
            page.click('button[type="submit"]')
        except:
            try:
                page.click('button:has-text("Login")')
            except:
                page.click('input[type="submit"]')
        
        # Wait for navigation to review page or dashboard
        page.wait_for_url(lambda url: "/review" in url or "/dashboard" in url, timeout=10000)
        
        return True
    
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False


if __name__ == "__main__":
    main()

