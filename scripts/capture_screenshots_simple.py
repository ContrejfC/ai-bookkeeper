#!/usr/bin/env python3
"""
Simple screenshot capture - no login required.
Captures whatever pages are accessible.
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    base_url = "https://ai-bookkeeper-app.onrender.com"
    output_dir = Path.home() / "Desktop" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Simple list of pages to try
    pages = [
        ("/", "01_homepage.png"),
        ("/login", "02_login_page.png"),
        ("/healthz", "03_healthz.png"),
        ("/readyz", "04_readyz.png"),
    ]
    
    print(f"📸 Capturing screenshots from {base_url}")
    print(f"   Output: {output_dir}")
    print("")
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.set_default_timeout(30000)
        
        captured = 0
        for path, filename in pages:
            url = f"{base_url}{path}"
            out_path = output_dir / filename
            
            print(f"📸 {filename}")
            print(f"   URL: {url}")
            
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)  # Wait for any JS to finish
                page.screenshot(path=str(out_path), full_page=True)
                print(f"   ✅ Saved")
                captured += 1
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print("")
        
        browser.close()
    
    print(f"✅ Captured {captured}/{len(pages)} screenshots")
    print(f"📁 Location: {output_dir}")
    
    if captured == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

