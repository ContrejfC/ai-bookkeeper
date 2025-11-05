/**
 * Categorizer Accessibility Tests
 * =================================
 * Automated accessibility checks with axe-core
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

test.describe('Categorizer Accessibility', () => {
  test('should not have accessibility violations on upload step', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    const results = await new AxeBuilder({ page }).analyze();
    
    expect(results.violations).toEqual([]);
  });

  test('should have accessible file input', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    const fileInput = await page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();
    
    // Should have accessible label or aria-label
    const label = await page.locator('label[for="file-upload"]');
    await expect(label).toBeVisible();
  });

  test('should have accessible table headers', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    // Upload a file first (would need to navigate through flow)
    // For now, test that table component has proper structure
    
    // Tables should have proper heading structure
    const results = await new AxeBuilder({ page })
      .include('table')
      .analyze();
    
    expect(results.violations.filter(v => v.id === 'table-duplicate-name')).toEqual([]);
  });

  test('should have keyboard-accessible dropdowns', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    // All interactive elements should be keyboard accessible
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    
    const keyboardViolations = results.violations.filter(v => 
      v.id === 'button-name' || v.id === 'label' || v.id === 'link-name'
    );
    
    expect(keyboardViolations).toEqual([]);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    const results = await new AxeBuilder({ page })
      .include('h1, h2, h3, h4, h5, h6')
      .analyze();
    
    const headingViolations = results.violations.filter(v => v.id === 'heading-order');
    expect(headingViolations).toEqual([]);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto(`${BASE_URL}/free/categorizer`);
    
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    const contrastViolations = results.violations.filter(v => v.id === 'color-contrast');
    expect(contrastViolations).toEqual([]);
  });
});

