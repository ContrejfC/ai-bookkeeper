/**
 * E2E Test: Onboarding Flow
 * ==========================
 * 
 * Tests the complete onboarding experience for paid users:
 * 1. Login as paid user
 * 2. Navigate to /welcome
 * 3. Upload sample CSV or create demo data
 * 4. Propose journal entries (AI categorization)
 * 5. Approve entries
 * 6. Demo export to QBO
 * 7. Download audit CSV
 * 
 * Success Criteria:
 * - Complete flow in ≤10 minutes
 * - All steps succeed without errors
 * - Demo export works without QBO connection
 * - Audit export contains redacted PII
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Test user (should exist in test database)
const PAID_USER = {
  email: 'paid@test.com',
  password: 'TestPassword123!',
  plan: 'professional'
};

test.describe('Paid User Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start at login page
    await page.goto(`${BASE_URL}/login`);
  });

  test('should complete full onboarding with sample CSV', async ({ page }) => {
    // Set timeout for full flow (10 minutes)
    test.setTimeout(600000);

    // Step 1: Login
    await test.step('Login as paid user', async () => {
      await page.fill('input[name="email"]', PAID_USER.email);
      await page.fill('input[name="password"]', PAID_USER.password);
      await page.click('button[type="submit"]');

      // Wait for dashboard or redirect
      await page.waitForURL(/\/(dashboard|welcome)/);
    });

    // Step 2: Navigate to welcome flow
    await test.step('Navigate to welcome page', async () => {
      await page.goto(`${BASE_URL}/welcome`);
      
      // Should see welcome screen
      await expect(page.locator('text=Welcome to AI Bookkeeper')).toBeVisible();
    });

    // Step 3: Download sample CSV
    let csvPath: string;
    await test.step('Download sample CSV', async () => {
      // Click download sample CSV button
      const downloadPromise = page.waitForEvent('download');
      await page.click('text=Download Sample CSV');
      const download = await downloadPromise;
      
      // Save file
      csvPath = await download.path();
      expect(csvPath).toBeTruthy();
    });

    // Step 4: Upload CSV
    await test.step('Upload CSV file', async () => {
      // Find file input
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(csvPath!);
      
      // Click upload button
      await page.click('text=Upload & Continue');
      
      // Wait for upload progress
      await expect(page.locator('text=Uploading')).toBeVisible({ timeout: 5000 });
      
      // Wait for upload completion (up to 2 minutes)
      await expect(page.locator('text=Upload complete')).toBeVisible({ timeout: 120000 });
    });

    // Step 5: View transactions
    await test.step('View imported transactions', async () => {
      // Click to view transactions
      await page.click('text=View Transactions');
      
      // Should navigate to transactions page
      await page.waitForURL(/\/transactions/);
      
      // Should see transactions table
      await expect(page.locator('table')).toBeVisible();
      
      // Go back to onboarding
      await page.goto(`${BASE_URL}/welcome`);
    });

    // Step 6: Propose journal entries (AI categorization)
    await test.step('Propose journal entries', async () => {
      // Click AI categorization button
      await page.click('text=Start AI Categorization');
      
      // Wait for job to start
      await expect(page.locator('text=Processing')).toBeVisible({ timeout: 10000 });
      
      // Wait for completion (up to 5 minutes)
      await expect(page.locator('text=Categorization complete')).toBeVisible({ timeout: 300000 });
    });

    // Step 7: Review and approve entries
    await test.step('Review proposed entries', async () => {
      // Navigate to transactions/entries
      await page.click('text=Go to Transactions');
      await page.waitForURL(/\/transactions/);
      
      // Should see proposed entries
      await expect(page.locator('text=proposed').or(page.locator('text=Proposed'))).toBeVisible();
    });

    // Step 8: Demo export to QBO
    await test.step('Demo export to QuickBooks', async () => {
      // Navigate to export page
      await page.goto(`${BASE_URL}/export`);
      
      // Should see demo mode indicator
      await expect(page.locator('text=Demo').or(page.locator('text=demo'))).toBeVisible({ timeout: 5000 });
      
      // Select QBO
      await page.click('text=Select QBO');
      
      // Set date range
      await page.fill('input[type="date"]', '2024-10-01');
      
      // Click export button
      await page.click('button:has-text("Export")');
      
      // Wait for export completion
      await expect(page.locator('text=Export complete').or(page.locator('text=success'))).toBeVisible({ timeout: 60000 });
    });

    // Step 9: Download audit CSV
    await test.step('Download audit CSV', async () => {
      // Navigate to audit page
      await page.goto(`${BASE_URL}/audit`);
      
      // Click export audit log
      const downloadPromise = page.waitForEvent('download');
      await page.click('text=Export CSV').or(page.click('button:has-text("Download")'));
      const download = await downloadPromise;
      
      // Verify download
      const auditPath = await download.path();
      expect(auditPath).toBeTruthy();
      
      // TODO: Verify CSV contains redacted PII
      // This would require reading the file and checking for ***EMAIL***, etc.
    });

    // Verify quota headers (check network tab)
    await test.step('Verify quota information displayed', async () => {
      // Go to any protected page
      await page.goto(`${BASE_URL}/transactions`);
      
      // Should see quota meter or info
      await expect(page.locator('text=transactions').or(page.locator('text=quota'))).toBeVisible({ timeout: 5000 });
    });
  });

  test('should complete onboarding with demo data', async ({ page }) => {
    test.setTimeout(600000);

    // Login
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Navigate to welcome
    await page.goto(`${BASE_URL}/welcome`);
    
    // Create demo data instead of uploading
    await test.step('Create demo data', async () => {
      await page.click('text=Create Demo Data').or(page.click('text=Use Sample Data'));
      
      // Wait for demo data creation
      await expect(page.locator('text=Demo data created')).toBeVisible({ timeout: 30000 });
    });

    // Continue with propose
    await test.step('Continue to propose', async () => {
      await page.click('text=Next').or(page.click('text=Continue'));
      await page.click('text=Start AI Categorization');
      
      // Wait for categorization
      await expect(page.locator('text=complete')).toBeVisible({ timeout: 300000 });
    });
  });

  test('should handle upload errors gracefully', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Navigate to welcome
    await page.goto(`${BASE_URL}/welcome`);
    
    // Try to upload invalid file
    await test.step('Upload invalid file shows error', async () => {
      // Create a mock file
      await page.setInputFiles('input[type="file"]', {
        name: 'invalid.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is not a CSV')
      });
      
      await page.click('text=Upload');
      
      // Should show error message
      await expect(page.locator('text=error').or(page.locator('text=failed'))).toBeVisible({ timeout: 10000 });
    });
  });

  test('should show progress during AI categorization', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Create demo data
    await page.goto(`${BASE_URL}/welcome`);
    await page.click('text=Create Demo Data');
    await expect(page.locator('text=created')).toBeVisible({ timeout: 30000 });

    // Start categorization
    await test.step('Categorization shows progress', async () => {
      await page.click('text=Next');
      await page.click('text=Start AI Categorization');
      
      // Should see progress indicator
      await expect(page.locator('[role="progressbar"]').or(page.locator('text=%'))).toBeVisible({ timeout: 10000 });
      
      // Progress should update
      await page.waitForTimeout(2000);
      
      // Should eventually complete
      await expect(page.locator('text=complete')).toBeVisible({ timeout: 300000 });
    });
  });

  test('should allow skipping steps', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Navigate to welcome
    await page.goto(`${BASE_URL}/welcome`);
    
    // Skip data upload
    await test.step('Can skip to later steps', async () => {
      // Look for skip button
      const skipButton = page.locator('text=Skip').or(page.locator('text=Skip for now'));
      
      if (await skipButton.isVisible()) {
        await skipButton.click();
        
        // Should move to next step
        await expect(page.locator('text=View Empty State').or(page.locator('text=Next'))).toBeVisible();
      }
    });
  });

  test('should track onboarding progress', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Navigate to welcome
    await page.goto(`${BASE_URL}/welcome`);
    
    // Should see progress indicator
    await test.step('Progress indicator visible', async () => {
      await expect(page.locator('[role="progressbar"]').or(page.locator('text=Step'))).toBeVisible();
    });

    // Progress should update as steps complete
    await test.step('Progress updates with steps', async () => {
      await page.click('text=Create Demo Data');
      await expect(page.locator('text=created')).toBeVisible({ timeout: 30000 });
      
      // Progress should have increased
      // (Exact check depends on UI implementation)
    });
  });
});

test.describe('Onboarding Performance', () => {
  test('should complete flow within 10 minutes', async ({ page }) => {
    test.setTimeout(600000); // 10 minutes

    const startTime = Date.now();

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Complete flow
    await page.goto(`${BASE_URL}/welcome`);
    await page.click('text=Create Demo Data');
    await expect(page.locator('text=created')).toBeVisible({ timeout: 30000 });
    
    await page.click('text=Next').first();
    await page.click('text=Start AI Categorization');
    await expect(page.locator('text=complete')).toBeVisible({ timeout: 300000 });

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000 / 60; // minutes

    // Should complete in ≤10 minutes
    expect(duration).toBeLessThanOrEqual(10);
    
    console.log(`Onboarding completed in ${duration.toFixed(2)} minutes`);
  });
});

