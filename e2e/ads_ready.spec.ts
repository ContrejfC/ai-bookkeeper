/**
 * E2E smoke tests for ad-ready go-live
 * 
 * Run with: npx playwright test e2e/ads_ready.spec.ts
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://app.ai-bookkeeper.app';
const API_URL = process.env.API_URL || 'https://api.ai-bookkeeper.app';

test.describe('Ad-Ready Go-Live Tests', () => {
  
  test('GPT Bridge page loads and fires analytics events', async ({ page }) => {
    // Listen for GA4 events
    const ga4Events: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('[GA4]')) {
        ga4Events.push(msg.text());
      }
    });
    
    // Navigate to GPT bridge
    await page.goto(`${BASE_URL}/gpt-bridge`);
    
    // Check page loaded
    await expect(page).toHaveTitle(/Run AI Bookkeeper in ChatGPT/);
    await expect(page.locator('h1')).toContainText('Run AI Bookkeeper in ChatGPT');
    
    // Verify bridge_viewed event fired
    await page.waitForTimeout(1000); // Wait for analytics
    expect(ga4Events.some(e => e.includes('bridge_viewed'))).toBeTruthy();
    
    // Click "Open in ChatGPT" button
    const gptButton = page.locator('button:has-text("Open in ChatGPT"), a:has-text("Open in ChatGPT")').first();
    await expect(gptButton).toBeVisible();
    
    // Click and verify event
    await gptButton.click();
    await page.waitForTimeout(500);
    expect(ga4Events.some(e => e.includes('open_gpt_clicked'))).toBeTruthy();
  });
  
  test('CSV Cleaner uploads file and shows preview', async ({ page }) => {
    const ga4Events: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('[GA4]')) {
        ga4Events.push(msg.text());
      }
    });
    
    // Navigate to CSV cleaner
    await page.goto(`${BASE_URL}/tools/csv-cleaner`);
    
    // Check page loaded
    await expect(page.locator('h1')).toContainText('CSV Transaction Cleaner');
    
    // Verify tool_opened event
    await page.waitForTimeout(1000);
    expect(ga4Events.some(e => e.includes('tool_opened'))).toBeTruthy();
    
    // Create a sample CSV file
    const csvContent = [
      'date,payee,memo,amount',
      '2024-01-15,Amazon,Office supplies,125.50',
      '2024-01-16,Starbucks,Coffee meeting,35.00',
      '2024-01-17,Rent Payment,Monthly office rent,2500.00'
    ].join('\n');
    
    // Upload CSV
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-transactions.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent)
    });
    
    // Wait for processing (max 10 seconds)
    const startTime = Date.now();
    await page.waitForSelector('table', { timeout: 10000 });
    const uploadTime = Date.now() - startTime;
    
    // Verify preview loaded in under 10 seconds
    expect(uploadTime).toBeLessThan(10000);
    
    // Check preview table exists
    await expect(page.locator('table')).toBeVisible();
    
    // Verify rows_previewed event
    await page.waitForTimeout(500);
    expect(ga4Events.some(e => e.includes('rows_previewed'))).toBeTruthy();
    
    // Verify table has data
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    expect(rowCount).toBeLessThanOrEqual(50); // Max 50 rows
  });
  
  test('CSV Cleaner export shows paywall', async ({ page }) => {
    const ga4Events: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('[GA4]')) {
        ga4Events.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/tools/csv-cleaner`);
    
    // Upload sample CSV
    const csvContent = 'date,payee,amount\n2024-01-15,Test,100';
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent)
    });
    
    // Wait for preview
    await page.waitForSelector('table', { timeout: 10000 });
    
    // Click Export CSV button (should be disabled/paywalled)
    const exportButton = page.locator('button:has-text("Export CSV")').first();
    await expect(exportButton).toBeVisible();
    await exportButton.click();
    
    // Verify paywall modal appears
    await page.waitForTimeout(500);
    const modal = page.locator('[role="dialog"], .modal');
    
    // Check if modal exists or if export_paywalled event fired
    const modalVisible = await modal.isVisible().catch(() => false);
    const eventFired = ga4Events.some(e => e.includes('export_paywalled'));
    
    expect(modalVisible || eventFired).toBeTruthy();
  });
  
  test('Pricing page loads and displays all plans', async ({ page }) => {
    await page.goto(`${BASE_URL}/pricing`);
    
    // Check page title
    await expect(page.locator('h1')).toContainText(/Pricing|Simple, Transparent Pricing/);
    
    // Verify all plan cards are visible
    await expect(page.locator('text=Starter')).toBeVisible();
    await expect(page.locator('text=Team')).toBeVisible();
    await expect(page.locator('text=Firm')).toBeVisible();
    await expect(page.locator('text=Enterprise')).toBeVisible();
    
    // Verify pricing
    await expect(page.locator('text=$49')).toBeVisible(); // Starter
    await expect(page.locator('text=$149')).toBeVisible(); // Team
    await expect(page.locator('text=$499')).toBeVisible(); // Firm
    
    // Verify pilot offer
    await expect(page.locator('text=$99')).toBeVisible(); // Pilot
    await expect(page.locator('text=/Pilot|Limited.*Offer/i')).toBeVisible();
  });
  
  test('Stripe checkout flow (Starter plan)', async ({ page }) => {
    const ga4Events: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('[GA4]')) {
        ga4Events.push(msg.text());
      }
    });
    
    await page.goto(`${BASE_URL}/pricing`);
    
    // Click "Start Starter" button
    const starterButton = page.locator('button:has-text("Start Starter")').first();
    await expect(starterButton).toBeVisible();
    await starterButton.click();
    
    // Verify checkout_clicked event
    await page.waitForTimeout(500);
    expect(ga4Events.some(e => e.includes('checkout_clicked'))).toBeTruthy();
    
    // Wait for redirect to Stripe Checkout or checkout page
    await page.waitForTimeout(2000);
    
    // Verify we're on Stripe checkout or got a checkout URL
    const currentUrl = page.url();
    const isStripeCheckout = currentUrl.includes('checkout.stripe.com') || 
                            currentUrl.includes('/checkout') ||
                            currentUrl.includes('/success');
    
    expect(isStripeCheckout).toBeTruthy();
  });
  
  test('Success page loads and fires purchase events', async ({ page }) => {
    const ga4Events: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('[GA4]')) {
        ga4Events.push(msg.text());
      }
    });
    
    // Navigate to success page with query params
    await page.goto(`${BASE_URL}/success?plan=starter&amount=49`);
    
    // Check page loaded
    await expect(page.locator('h1')).toContainText(/Welcome|Success/i);
    
    // Verify purchase and subscription_started events fired
    await page.waitForTimeout(1000);
    expect(ga4Events.some(e => e.includes('purchase'))).toBeTruthy();
    expect(ga4Events.some(e => e.includes('subscription_started'))).toBeTruthy();
    
    // Verify next steps are shown
    await expect(page.locator('text=/Next Steps|Getting Started/i')).toBeVisible();
  });
  
  test('Legal pages are accessible', async ({ page }) => {
    // Privacy Policy
    await page.goto(`${BASE_URL}/privacy`);
    await expect(page.locator('h1')).toContainText('Privacy Policy');
    
    // Terms of Service
    await page.goto(`${BASE_URL}/terms`);
    await expect(page.locator('h1')).toContainText('Terms of Service');
    
    // DPA
    await page.goto(`${BASE_URL}/dpa`);
    await expect(page.locator('h1')).toContainText('Data Processing Agreement');
    
    // Security
    await page.goto(`${BASE_URL}/security`);
    await expect(page.locator('h1')).toContainText('Security');
  });
  
  test('API health check responds', async ({ request }) => {
    const response = await request.get(`${API_URL}/healthz`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('message');
    expect(data).toHaveProperty('version');
  });
  
  test('Sitemap and robots.txt are accessible', async ({ request }) => {
    // Sitemap
    const sitemapResponse = await request.get(`${BASE_URL}/sitemap.xml`);
    expect(sitemapResponse.ok()).toBeTruthy();
    const sitemapText = await sitemapResponse.text();
    expect(sitemapText).toContain('<?xml');
    expect(sitemapText).toContain('/pricing');
    expect(sitemapText).toContain('/gpt-bridge');
    
    // Robots.txt
    const robotsResponse = await request.get(`${BASE_URL}/robots.txt`);
    expect(robotsResponse.ok()).toBeTruthy();
    const robotsText = await robotsResponse.text();
    expect(robotsText).toContain('User-agent');
    expect(robotsText).toContain('Sitemap');
  });
  
});

