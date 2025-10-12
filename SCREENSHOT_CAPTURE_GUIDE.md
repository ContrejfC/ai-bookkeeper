# Screenshot Capture Guide

**Phase:** 2b Post-Deployment  
**Required Screenshots:** 7 total  
**Estimated Time:** 15-20 minutes

---

## Prerequisites

1. **Server Running:**
   ```bash
   cd /path/to/ai-bookkeeper
   uvicorn app.api.main:app --port 8000
   ```

2. **Authenticated User:**
   - Owner role account
   - Valid JWT token

3. **Browser:**
   - Chrome, Firefox, or Safari
   - DevTools available (for high-DPI screenshots)

4. **Fixtures Present:**
   - `tests/fixtures/receipts/` (text receipts)
   - `tests/fixtures/receipts_pdf/` (PDF receipts)

---

## Screenshot Checklist

### 1. Onboarding Wizard (4 screenshots)

#### Step 1: Chart of Accounts
**URL:** `http://localhost:8000/onboarding`

**Capture:**
- Full wizard interface
- Progress indicator showing "1. Chart of Accounts"
- Both template and upload options visible
- Template dropdown expanded (Standard Small Business selected)

**Save As:** `artifacts/onboarding/step1_coa.png`

**Settings:**
- Resolution: 1920x1080 or higher
- Full page screenshot or viewport only
- Include browser chrome (optional)

---

#### Step 2: Data Ingest
**Actions:**
1. Select "Standard Small Business" template
2. Click "Next"
3. Wait for Step 2 to load

**Capture:**
- Progress indicator showing "2. Data Ingest"
- Transactions upload field
- Receipts upload field (multiple files)
- File format hints visible

**Save As:** `artifacts/onboarding/step2_ingest.png`

---

#### Step 3: Safety Settings
**Actions:**
1. Upload a sample transactions CSV (create minimal if needed)
2. Click "Next"
3. Wait for Step 3 to load

**Capture:**
- Progress indicator showing "3. Safety Settings"
- Threshold slider at 0.90
- LLM budget input showing $50
- AUTOPOST disabled checkbox (checked and disabled)
- Yellow warning banner visible

**Save As:** `artifacts/onboarding/step3_settings.png`

---

#### Step 4: Tips & Finish
**Actions:**
1. Keep default settings (0.90, $50)
2. Click "Next"
3. Wait for Step 4 to load

**Capture:**
- Progress indicator showing "4. Tips & Finish"
- Keyboard shortcuts section
- Shadow mode explanation
- Monitor performance tip
- "Start Reviewing Transactions →" button (green, prominent)

**Save As:** `artifacts/onboarding/step4_finish.png`

---

### 2. Receipt Highlights (1 screenshot)

#### Receipt Overlay Example
**URL:** `http://localhost:8000/receipts`

**Actions:**
1. Wait for receipts list to load
2. Click on first receipt in list
3. Ensure "Show Overlays" is checked
4. Hover over one bbox to show tooltip

**Capture:**
- Receipt list sidebar (left) with multiple receipts
- PDF viewer (center) with receipt displayed
- Colored bbox overlays visible:
  - Blue box on date
  - Green box on amount
  - Purple box on vendor
  - Yellow box on total
- Hover tooltip showing field value + confidence
- Legend (top right) showing color meanings
- Field summary cards below PDF

**Save As:** `artifacts/receipts/overlay_sample.png`

**Notes:**
- Use a receipt with all 4 fields successfully detected
- Ensure overlays are clearly visible (not too faint)
- Tooltip should be in frame

---

### 3. Product Analytics (1 screenshot)

#### Analytics Dashboard (7-Day View)
**URL:** `http://localhost:8000/analytics`

**Actions:**
1. If no real events, page will show sample data
2. Wait for all data to load
3. Scroll to show at least 2 daily report cards

**Capture:**
- Page title "Product Analytics"
- Summary cards at top:
  - Total Events (number)
  - Active Tenants (number)
  - Page Views (number)
  - Reviews (number)
- At least 2 daily report cards:
  - Date header
  - Event totals grid (Page Views, Approvals, Rejections, Exports)
  - Per-tenant breakdown (if available)
- Sample data notice (if present)

**Save As:** `artifacts/analytics/dashboard.png`

**Notes:**
- Full page screenshot preferred
- Include summary cards and daily reports
- Sample data banner is OK for initial deployment

---

### 4. Navigation (Bonus)

#### Header Navigation
**URL:** Any authenticated page (e.g., `/firm`)

**Capture:**
- Full header nav bar showing all links:
  - Firm
  - Review
  - Rules
  - Audit Log
  - Receipts (newly added)
  - Analytics (newly added)
  - Billing
  - Notifications
  - Onboarding (indigo color, Owner only)

**Save As:** `artifacts/navigation/header.png` (optional)

---

## Screenshot Techniques

### Method 1: Browser DevTools (Recommended)
```javascript
// Open DevTools Console (F12)
// Run this to take full-page screenshot:

// Chrome/Edge
// 1. Open DevTools (F12)
// 2. Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
// 3. Type "screenshot"
// 4. Select "Capture full size screenshot"

// Firefox
// 1. Open DevTools (F12)
// 2. Click three-dot menu → "Take a screenshot"
// 3. Select "Save full page"
```

### Method 2: Browser Extensions
- **Awesome Screenshot** (Chrome, Firefox)
- **Fireshot** (Chrome, Firefox)
- **Nimbus** (Chrome)

### Method 3: Command Line (Playwright)
```python
# install: pip install playwright && playwright install
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:8000/onboarding')
    page.screenshot(path='artifacts/onboarding/step1_coa.png', full_page=True)
    browser.close()
```

---

## Screenshot Specifications

**Format:** PNG (preferred) or JPEG  
**Resolution:** Minimum 1280x720, recommended 1920x1080  
**Color Depth:** 24-bit RGB  
**Compression:** Lossless for PNG, quality 90+ for JPEG  
**File Size:** < 5MB per screenshot

---

## Verification Checklist

Before submitting screenshots:

- [ ] All 7 screenshots captured (4 onboarding + 1 receipts + 1 analytics + 1 nav)
- [ ] File names match exactly (case-sensitive)
- [ ] Images are clear and readable
- [ ] No sensitive data visible (passwords, real emails, etc.)
- [ ] Artifacts directory structure:
  ```
  artifacts/
  ├── onboarding/
  │   ├── step1_coa.png
  │   ├── step2_ingest.png
  │   ├── step3_settings.png
  │   └── step4_finish.png
  ├── receipts/
  │   └── overlay_sample.png
  └── analytics/
      └── dashboard.png
  ```
- [ ] Files committed to repo or uploaded to artifacts bucket

---

## Troubleshooting

**Issue:** Server not responding  
**Solution:** Check server logs, verify port 8000 not in use

**Issue:** Authentication required  
**Solution:** Use dev login endpoint to get token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "magic_token": "dev"}'
```

**Issue:** Receipts not loading  
**Solution:** Verify fixtures exist in `tests/fixtures/receipts_pdf/`

**Issue:** Analytics shows "No data"  
**Solution:** This is expected initially; sample data banner is OK

**Issue:** Overlays not visible  
**Solution:** 
- Check "Show Overlays" toggle
- Verify receipt has extracted fields (check API response)
- Try different receipt

---

## Post-Capture

After capturing all screenshots:

1. **Review for Quality:**
   - Check clarity and readability
   - Verify no sensitive data visible
   - Ensure UI elements are in focus

2. **Commit to Repository:**
   ```bash
   git add artifacts/
   git commit -m "Add Phase 2b screenshots"
   git push
   ```

3. **Or Upload to Artifacts Bucket:**
   ```bash
   aws s3 sync artifacts/ s3://ai-bookkeeper-artifacts/phase2b/
   ```

4. **Update Delivery Report:**
   - Add screenshot links to PHASE2B_FINAL_DELIVERY.md
   - Check off screenshot items in deployment checklist

---

**Estimated Time:** 15-20 minutes for all 7 screenshots  
**Priority:** High (required for deployment acceptance)  
**Next Step:** See PILOT_ENABLEMENT.md

