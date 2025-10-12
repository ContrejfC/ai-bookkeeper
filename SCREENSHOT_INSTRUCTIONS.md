# Screenshot Capture Instructions

**Status:** Manual capture required (Playwright not installed)  
**Target:** 33 screenshots (start with 9 priority)  
**Deadline:** Today

---

## Quick Start (9 Priority Screenshots)

### Prerequisites
1. Server running: `python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000`
2. Login as: `owner@pilot-smb-001.demo` / `demo-password-123`
3. UI_ASSESSMENT=1 banner visible

### Priority Shots (Minimum for Review)

#### 1. Review Page with Filters
```
URL: http://localhost:8000/review
File: artifacts/ui-assessment/03_review_default.png
Notes: Default view with transaction list
```

#### 2-4. Review Filtered by Reason
```
URLs: 
  - /review?reason=below_threshold
  - /review?reason=cold_start  
  - /review?reason=imbalance
Files: 04_review_below_threshold.png, 05_review_cold_start.png, 06_review_imbalance.png
Notes: Show different reason filters in action
```

#### 5-6. Receipt Overlays
```
URLs:
  - /receipts (click first clean receipt)
  - /receipts (click first messy receipt)
Files: 13_receipts_clean_overlay.png, 14_receipts_messy_overlay.png
Notes: Show bounding box overlays with different confidence levels
```

#### 7. Analytics Dashboard
```
URL: /analytics
File: 16_analytics_dashboard.png
Notes: Show event counts and tenant breakdown
```

#### 8. Firm Console
```
URL: /firm
File: 18_firm_console_owner.png
Notes: Owner view with tenant list
```

#### 9. Onboarding Step 1
```
URL: /onboarding
File: 26_onboarding_step1.png
Notes: Chart of Accounts selection step
```

---

## Capture Methods

### Method 1: Browser DevTools (Recommended)

**Chrome / Edge:**
1. Open DevTools (F12 or Cmd+Option+I)
2. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
3. Type "screenshot" → Select "Capture full size screenshot"
4. Image saves to Downloads folder
5. Rename and move to `artifacts/ui-assessment/`

**Firefox:**
1. Open DevTools (F12)
2. Click "..." menu → "Take a screenshot"
3. Choose "Save full page"
4. Rename and move to `artifacts/ui-assessment/`

**Safari:**
1. Enable Develop menu: Preferences → Advanced → Show Develop menu
2. Develop → Show Web Inspector
3. Right-click page → Inspect Element
4. Use Screenshot button in toolbar

### Method 2: macOS Built-in

```bash
# Full window
Cmd+Shift+4, then press Space, click window

# Selected area
Cmd+Shift+4, drag to select

# Timed (5 seconds)
Cmd+Shift+5, Options → 5-second timer
```

### Method 3: CLI Screenshot Tool

```bash
# Install (if needed)
brew install webkit2png

# Capture
webkit2png -F http://localhost:8000/review
mv review-full.png artifacts/ui-assessment/03_review_default.png
```

---

## Full 33 Screenshot Checklist

Reference `artifacts/ui-assessment/screenshot_manifest.json` for complete list.

### Home (2)
- [ ] 01_home_logged_out.png
- [ ] 02_home_logged_in_owner.png

### Review (6)
- [ ] 03_review_default.png ⭐ PRIORITY
- [ ] 04_review_below_threshold.png ⭐ PRIORITY
- [ ] 05_review_cold_start.png ⭐ PRIORITY
- [ ] 06_review_imbalance.png ⭐ PRIORITY
- [ ] 07_review_empty_state.png
- [ ] 08_review_detail_modal.png

### Metrics (3)
- [ ] 09_metrics_default.png
- [ ] 10_metrics_7d.png
- [ ] 11_metrics_30d.png

### Receipts (4)
- [ ] 12_receipts_list.png
- [ ] 13_receipts_clean_overlay.png ⭐ PRIORITY
- [ ] 14_receipts_messy_overlay.png ⭐ PRIORITY
- [ ] 15_receipts_hover_tooltip.png

### Analytics (2)
- [ ] 16_analytics_dashboard.png ⭐ PRIORITY
- [ ] 17_analytics_per_tenant.png

### Firm Console (2)
- [ ] 18_firm_console_owner.png ⭐ PRIORITY
- [ ] 19_firm_console_staff_denied.png

### Rules Console (3)
- [ ] 20_rules_list.png
- [ ] 21_rules_add_modal.png
- [ ] 22_rules_edit_modal.png

### Audit Log (3)
- [ ] 23_audit_default.png
- [ ] 24_audit_filtered.png
- [ ] 25_audit_export_csv.png

### Onboarding (4)
- [ ] 26_onboarding_step1.png ⭐ PRIORITY
- [ ] 27_onboarding_step2.png
- [ ] 28_onboarding_step3.png
- [ ] 29_onboarding_step4.png

### Auth (2)
- [ ] 30_login_page.png
- [ ] 31_login_error.png

### Accessibility (2)
- [ ] 32_keyboard_nav_focus.png
- [ ] 33_ui_assessment_banner.png

---

## Naming Convention

Format: `##_page_description.png`

Examples:
- `03_review_default.png` (not `review.png`)
- `13_receipts_clean_overlay.png` (not `receipt1.png`)

Match names exactly as defined in `screenshot_manifest.json`.

---

## Quality Checklist

Before committing screenshots:

- [ ] Resolution: 1920x1080 or higher
- [ ] Format: PNG (not JPEG)
- [ ] No personal browser bookmarks/tabs visible
- [ ] UI_ASSESSMENT=1 banner visible
- [ ] Demo data showing (not empty states unless specified)
- [ ] Focus states visible where relevant
- [ ] No PII in screenshots (demo emails only)
- [ ] Filenames match manifest exactly

---

## Committing Screenshots

```bash
cd ~/ai-bookkeeper

# Verify files present
ls -lh artifacts/ui-assessment/*.png | wc -l
# Should show at least 9 (priority) or 33 (complete)

# Stage screenshots
git add artifacts/ui-assessment/*.png

# Commit with descriptive message
git commit -m "Add UI assessment screenshots (9 priority / 33 total)

- Review page with reason filters
- Receipt bounding box overlays  
- Analytics dashboard
- Firm console owner view
- Onboarding wizard step 1
- All screenshots captured at 1920x1080
- UI_ASSESSMENT=1 banner visible
- No PII present"
```

---

## Automation for Sprint 12

**Recommendation:** Install Playwright for automated capture

```bash
pip3 install playwright
playwright install chromium

# Then use capture_screenshots.py
python3 scripts/capture_screenshots.py
```

**Benefits:**
- Consistent resolution and quality
- Automated capture of all 33 in < 5 minutes
- Easy to re-run after UI changes
- Can integrate into CI/CD pipeline

**Estimated Setup:** 30 minutes  
**Time Saved per Run:** ~45 minutes (vs manual capture)

---

**Last Updated:** 2025-10-11  
**Status:** Manual capture method documented, Playwright recommended for Sprint 12

