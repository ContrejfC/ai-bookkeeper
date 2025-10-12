# Screenshot Capture for UI Assessment

## Manual Capture Instructions

Since Playwright is not installed in the current environment, screenshots can be captured manually:

### Using Browser Developer Tools (Recommended)

1. Open Chrome/Firefox DevTools (F12)
2. Open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
3. Type "screenshot" → Select "Capture full size screenshot"
4. Save to `artifacts/ui-assessment/` with naming from manifest

### Using macOS Screenshot Tool

```bash
# Full window capture
Cmd+Shift+4 → Space → Click window

# Rename and move
mv ~/Desktop/Screen\ Shot*.png artifacts/ui-assessment/01_home_logged_out.png
```

### Automated Capture (If Playwright is Available)

```bash
# Install Playwright
pip3 install playwright
playwright install chromium

# Run capture script
python3 scripts/capture_screenshots.py
```

## Screenshot Manifest

See `artifacts/ui-assessment/screenshot_manifest.json` for complete list of 33 required screenshots.

### Quick Reference

**Priority Screenshots (minimum viable):**
1. `03_review_default.png` - Review page with filters
2. `04-06_review_reasons.png` - All 3 reason filters (below_threshold, cold_start, imbalance)
3. `13-14_receipts_overlay.png` - Clean and messy receipt overlays
4. `16_analytics_dashboard.png` - Analytics default view
5. `18_firm_console_owner.png` - Firm console owner view
6. `26-29_onboarding_steps.png` - All 4 onboarding steps
7. `33_ui_assessment_banner.png` - UI Assessment mode banner

## Alternative: Video Walkthrough

If individual screenshots are time-consuming, record a screen recording:

```bash
# macOS
Cmd+Shift+5 → Record Selected Portion

# Or use QuickTime Player → File → New Screen Recording
```

Export key frames from the video at timestamps corresponding to each route.

## Verification

After capture, verify:
- [ ] All 33 screenshots present in `artifacts/ui-assessment/`
- [ ] Filenames match manifest (e.g., `01_home_logged_out.png`)
- [ ] Screenshots show actual data (not empty states)
- [ ] UI Assessment banner visible where applicable
- [ ] Images are 1920x1080 or higher resolution

## Storage

Screenshots are **excluded from git** via `.gitignore`. For sharing:

1. **Internal:** Upload to shared drive or Slack
2. **External:** Use Figma, Notion, or screenshot hosting service
3. **Archive:** Zip and store in `artifacts/` folder

```bash
cd artifacts/ui-assessment
zip -r ui_screenshots_$(date +%Y%m%d).zip *.png
```

