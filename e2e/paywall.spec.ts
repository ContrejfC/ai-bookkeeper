/**
 * E2E Test: Paywall Enforcement
 * ==============================
 * 
 * Tests that unpaid users are blocked from protected features.
 * 
 * Test Cases:
 * -----------
 * 1. Free tier blocked from /transactions
 * 2. Free tier blocked from /rules
 * 3. Free tier blocked from /export
 * 4. Free tier sees upgrade CTAs
 * 5. Free tier can view pricing page
 * 6. Quota exhausted users blocked
 * 7. Inactive subscription blocked
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';

const FREE_USER = {
  email: 'free@test.com',
  password: 'TestPassword123!'
};

const PAID_USER = {
  email: 'paid@test.com',
  password: 'TestPassword123!'
};

test.describe('Paywall Enforcement - Free Tier', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
  });

  test('should block free user from /transactions', async ({ page }) => {
    // Login as free user
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access transactions
    await page.goto(`${BASE_URL}/transactions`);

    // Should see upgrade message or redirect
    await expect(
      page.locator('text=upgrade').or(
        page.locator('text=subscription').or(
          page.locator('text=premium')
        )
      )
    ).toBeVisible({ timeout: 5000 });

    // Should NOT see actual transactions table
    const hasTable = await page.locator('table').count();
    if (hasTable > 0) {
      // If table exists, it should be blocked/disabled
      await expect(page.locator('text=Upgrade')).toBeVisible();
    }
  });

  test('should block free user from /rules', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access rules
    await page.goto(`${BASE_URL}/rules`);

    // Should see feature gate message
    await expect(
      page.locator('text=Professional plan').or(
        page.locator('text=advanced_rules').or(
          page.locator('text=Upgrade')
        )
      )
    ).toBeVisible({ timeout: 5000 });
  });

  test('should block free user from /export', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access export
    await page.goto(`${BASE_URL}/export`);

    // Should see upgrade message
    await expect(
      page.locator('text=qbo_export').or(
        page.locator('text=Professional').or(
          page.locator('text=Upgrade')
        )
      )
    ).toBeVisible({ timeout: 5000 });
  });

  test('should show upgrade CTA on gated features', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to any protected page
    await page.goto(`${BASE_URL}/transactions`);

    // Should see upgrade button
    const upgradeButton = page.locator('button:has-text("Upgrade")').or(
      page.locator('a:has-text("Upgrade")')
    );

    await expect(upgradeButton).toBeVisible({ timeout: 5000 });

    // Click upgrade button
    await upgradeButton.first().click();

    // Should navigate to pricing
    await page.waitForURL(/\/pricing/, { timeout: 5000 });
  });

  test('should allow free user to view pricing page', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Navigate to pricing
    await page.goto(`${BASE_URL}/pricing`);

    // Should see pricing plans
    await expect(page.locator('text=Starter').or(page.locator('text=Professional'))).toBeVisible();
    await expect(page.locator('text=month').or(page.locator('text=$/mo'))).toBeVisible();
  });

  test('should show current plan on protected pages', async ({ page }) => {
    // Login
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to transactions (with entitlement gate)
    await page.goto(`${BASE_URL}/transactions`);

    // Should show current plan (free)
    await expect(page.locator('text=free').or(page.locator('text=Free'))).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Paywall Enforcement - Quota Exhausted', () => {
  const QUOTA_USER = {
    email: 'quota_exhausted@test.com',
    password: 'TestPassword123!'
  };

  test('should block user with exhausted quota', async ({ page }) => {
    // Login as user with exhausted quota
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', QUOTA_USER.email);
    await page.fill('input[name="password"]', QUOTA_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access propose (write operation)
    await page.goto(`${BASE_URL}/transactions`);

    // Try to propose entries
    const proposeButton = page.locator('button:has-text("Propose")').or(
      page.locator('button:has-text("Categorize")')
    );

    if (await proposeButton.isVisible()) {
      await proposeButton.click();

      // Should see quota exceeded message
      await expect(
        page.locator('text=quota exceeded').or(
          page.locator('text=limit reached').or(
            page.locator('text=upgrade')
          )
        )
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test('should show quota meter approaching limit', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', QUOTA_USER.email);
    await page.fill('input[name="password"]', QUOTA_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to transactions
    await page.goto(`${BASE_URL}/transactions`);

    // Should see quota information
    await expect(
      page.locator('text=transactions').and(
        page.locator('text=/\\d+.*\\d+/')  // Number / Number format
      )
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Paywall Enforcement - Inactive Subscription', () => {
  const INACTIVE_USER = {
    email: 'inactive@test.com',
    password: 'TestPassword123!'
  };

  test('should block user with inactive subscription', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', INACTIVE_USER.email);
    await page.fill('input[name="password"]', INACTIVE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access protected page
    await page.goto(`${BASE_URL}/transactions`);

    // Should see inactive subscription message
    await expect(
      page.locator('text=inactive').or(
        page.locator('text=past_due').or(
          page.locator('text=update your billing')
        )
      )
    ).toBeVisible({ timeout: 5000 });

    // Should have "Manage Billing" button
    await expect(page.locator('button:has-text("Manage Billing")')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Paywall Enforcement - Paid User Access', () => {
  test('should allow paid user full access', async ({ page }) => {
    // Login as paid user
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Access transactions - should work
    await test.step('Can access transactions', async () => {
      await page.goto(`${BASE_URL}/transactions`);
      await expect(page.locator('table').or(page.locator('[role="table"]'))).toBeVisible({ timeout: 10000 });
    });

    // Access rules - should work
    await test.step('Can access rules', async () => {
      await page.goto(`${BASE_URL}/rules`);
      // Should NOT see upgrade message
      const upgradeVisible = await page.locator('text=Upgrade Plan').isVisible().catch(() => false);
      expect(upgradeVisible).toBeFalsy();
    });

    // Access export - should work
    await test.step('Can access export', async () => {
      await page.goto(`${BASE_URL}/export`);
      // Should see export options
      await expect(page.locator('text=QuickBooks').or(page.locator('text=Export'))).toBeVisible();
    });
  });

  test('should show quota usage for paid user', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', PAID_USER.email);
    await page.fill('input[name="password"]', PAID_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to transactions
    await page.goto(`${BASE_URL}/transactions`);

    // Should see quota meter
    await expect(
      page.locator('[role="progressbar"]').or(
        page.locator('text=transactions')
      )
    ).toBeVisible({ timeout: 5000 });

    // Should show plan name
    await expect(
      page.locator('text=professional').or(
        page.locator('text=Professional').or(
          page.locator('text=starter')
        )
      )
    ).toBeVisible();
  });
});

test.describe('Feature-Level Gating', () => {
  test('should gate advanced_rules feature', async ({ page }) => {
    // Login as starter (doesn't have advanced_rules)
    const STARTER_USER = {
      email: 'starter@test.com',
      password: 'TestPassword123!'
    };

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', STARTER_USER.email);
    await page.fill('input[name="password"]', STARTER_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to rules page
    await page.goto(`${BASE_URL}/rules`);

    // Should see feature gate
    await expect(
      page.locator('text=advanced_rules').or(
        page.locator('text=Professional plan')
      )
    ).toBeVisible({ timeout: 5000 });
  });

  test('should gate qbo_export feature', async ({ page }) => {
    // Login as starter (doesn't have qbo_export)
    const STARTER_USER = {
      email: 'starter@test.com',
      password: 'TestPassword123!'
    };

    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', STARTER_USER.email);
    await page.fill('input[name="password"]', STARTER_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to export page
    await page.goto(`${BASE_URL}/export`);

    // Should see feature gate
    await expect(
      page.locator('text=qbo_export').or(
        page.locator('text=Professional')
      )
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Soft vs Hard Blocking', () => {
  test('should soft-block (show message) on rules page', async ({ page }) => {
    // Login as free user
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', FREE_USER.email);
    await page.fill('input[name="password"]', FREE_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Go to rules
    await page.goto(`${BASE_URL}/rules`);

    // Should show message (soft block) but not redirect immediately
    await page.waitForTimeout(2000);
    
    // Should still be on rules page or see upgrade card
    const currentUrl = page.url();
    const isOnRulesOrSeeingGate = currentUrl.includes('/rules') || 
      await page.locator('text=Upgrade').isVisible();
    
    expect(isOnRulesOrSeeingGate).toBeTruthy();
  });

  test('should hard-block (redirect) on quota exhausted', async ({ page }) => {
    const EXHAUSTED_USER = {
      email: 'exhausted@test.com',
      password: 'TestPassword123!'
    };

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', EXHAUSTED_USER.email);
    await page.fill('input[name="password"]', EXHAUSTED_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|welcome)/);

    // Try to access write operation
    await page.goto(`${BASE_URL}/transactions`);

    // If quota truly exhausted with hard block, might redirect to pricing
    // Or show blocking modal
    await expect(
      page.locator('text=exceeded').or(
        page.locator('text=Upgrade Now')
      )
    ).toBeVisible({ timeout: 10000 });
  });
});

