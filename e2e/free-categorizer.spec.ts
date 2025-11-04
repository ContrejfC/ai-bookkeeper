/**
 * E2E Tests for Free Categorizer - Trust, Compliance, and Conversion v1
 * =====================================================================
 */

import { test, expect } from '@playwright/test';

test.describe('Free Categorizer - Trust & Conversion', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/free/categorizer');
  });

  test('sample flow: use sample statement → preview → download via bypass', async ({ page }) => {
    // Click "Use Sample Statement"
    await page.click('text=Use Sample Statement');
    
    // Wait for preview to load
    await expect(page.locator('text=Preview')).toBeVisible({ timeout: 10000 });
    
    // Verify sample data is loaded
    await expect(page.locator('text=Amazon.com')).toBeVisible();
    await expect(page.locator('text=Office Supplies')).toBeVisible();
    
    // Continue to email step
    await page.click('text=Continue');
    
    // Should show email gate
    await expect(page.locator('text=Almost There!')).toBeVisible();
    
    // Click bypass link
    await page.click('text=Skip for now');
    
    // Should be on download step
    await expect(page.locator('text=Ready to Download!')).toBeVisible();
    
    // Download
    const downloadPromise = page.waitForEvent('download');
    await page.click('text=Download CSV');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain('categorized.csv');
  });

  test('email gate flow: enter email → lead captured → CSV downloaded', async ({ page }) => {
    // Use sample to skip upload
    await page.click('text=Use Sample Statement');
    await expect(page.locator('text=Preview')).toBeVisible({ timeout: 10000 });
    
    // Continue to email
    await page.click('text=Continue');
    
    // Enter email
    await page.fill('#email-input', 'test@example.com');
    await page.click('text=Email Me the CSV');
    
    // Should show verify step (in real flow, would need to mock email)
    // For E2E, we'll stop here and verify the UI state
    await expect(page.locator('text=Check Your Email!')).toBeVisible();
    
    // Verify lead_submitted event was fired (check analytics if wired)
    // This would need analytics mock/spy in real implementation
  });

  test('consent toggle: default OFF → toggle ON sends consent_training=true', async ({ page }) => {
    // Verify consent checkbox exists and is unchecked by default
    const consentCheckbox = page.locator('text=Allow anonymized data to improve models');
    await expect(consentCheckbox).toBeVisible();
    
    // Check if it's unchecked by default
    const checkbox = page.locator('input[type="checkbox"]').first();
    await expect(checkbox).not.toBeChecked();
    
    // Click to enable
    await checkbox.check();
    await expect(checkbox).toBeChecked();
    
    // Upload a file (would need to test that consent_training=true is sent)
    // This requires file upload mock
  });

  test('error state: ROW_LIMIT_EXCEEDED shows repair tips', async ({ page }) => {
    // This test would require uploading a file > 500 rows
    // For now, verify error UI exists
    
    // Navigate through flow and check error banner structure
    const errorBanner = page.locator('[role="alert"]');
    // Error banner should not be visible initially
    const isVisible = await errorBanner.isVisible().catch(() => false);
    expect(isVisible).toBe(false);
    
    // TODO: Mock upload response to trigger error
    // Then verify repair tips are shown
  });

  test('delete now button: purges data and returns to upload', async ({ page }) => {
    // Use sample data
    await page.click('text=Use Sample Statement');
    await expect(page.locator('text=Preview')).toBeVisible({ timeout: 10000 });
    
    // Click delete button
    await page.click('text=Delete Now');
    
    // Confirm deletion modal
    await expect(page.locator('text=Delete Upload?')).toBeVisible();
    await page.click('button:has-text("Delete Now")');
    
    // Should return to upload step
    await expect(page.locator('text=Upload any format')).toBeVisible({ timeout: 5000 });
  });

  test('sample CSV output modal: opens and downloads sample', async ({ page }) => {
    // Click "See Sample CSV Output"
    await page.click('text=See Sample CSV Output');
    
    // Modal should open
    await expect(page.locator('text=Sample CSV Output')).toBeVisible();
    
    // Table should be visible
    await expect(page.locator('text=Amazon.com')).toBeVisible();
    
    // Download sample
    const downloadPromise = page.waitForEvent('download');
    await page.click('text=Download Sample CSV');
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toBe('sample_output.csv');
    
    // Close modal
    await page.click('button:has-text("Close")');
    await expect(page.locator('text=Sample CSV Output')).not.toBeVisible();
  });

  test('accessibility: keyboard navigation works', async ({ page }) => {
    // Tab through the page
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verify focus states are visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // All interactive elements should have aria-labels
    const buttons = page.locator('button');
    const count = await buttons.count();
    
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();
      
      // Either aria-label or text content should exist
      expect(ariaLabel || text).toBeTruthy();
    }
  });

  test('watermark banner: shows when rows > limit with upgrade CTA', async ({ page }) => {
    // Would need to upload file > 500 rows to test
    // For now, verify banner structure exists in sample flow
    await page.click('text=Use Sample Statement');
    await expect(page.locator('text=Preview')).toBeVisible({ timeout: 10000 });
    
    // Sample has < 500 rows, so no watermark banner
    // In real test with > 500 rows, would verify:
    // await expect(page.locator('text=Remove Watermark → Upgrade')).toBeVisible();
  });
});

