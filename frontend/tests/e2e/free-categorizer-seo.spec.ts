/**
 * Free Categorizer - SEO & UX Tests
 * =================================
 * 
 * Tests metadata, JSON-LD, OG tags, and core UX elements.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const CATEGORIZER_URL = `${BASE_URL}/free/categorizer`;

test.describe('Free Categorizer - SEO Metadata', () => {
  test('should have correct title tag', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const title = await page.title();
    expect(title).toBe('Free Bank Transaction Categorizer | CSV, OFX, QFX');
    expect(title.length).toBeLessThanOrEqual(60);
  });

  test('should have correct meta description', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const description = await page.locator('meta[name="description"]').getAttribute('content');
    expect(description).toContain('Upload CSV, OFX, or QFX');
    expect(description).toContain('QuickBooks');
    expect(description?.length || 0).toBeGreaterThanOrEqual(145);
    expect(description?.length || 0).toBeLessThanOrEqual(165);
  });

  test('should have canonical URL', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
    expect(canonical).toMatch(/\/free\/categorizer$/);
  });

  test('should have Open Graph tags', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    const ogDescription = await page.locator('meta[property="og:description"]').getAttribute('content');
    const ogUrl = await page.locator('meta[property="og:url"]').getAttribute('content');
    const ogType = await page.locator('meta[property="og:type"]').getAttribute('content');
    const ogImage = await page.locator('meta[property="og:image"]').getAttribute('content');
    
    expect(ogTitle).toBeTruthy();
    expect(ogDescription).toBeTruthy();
    expect(ogUrl).toMatch(/\/free\/categorizer$/);
    expect(ogType).toBe('website');
    expect(ogImage).toMatch(/\/api\/og\/free-categorizer/);
  });

  test('should have Twitter Card tags', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const twitterCard = await page.locator('meta[name="twitter:card"]').getAttribute('content');
    const twitterTitle = await page.locator('meta[name="twitter:title"]').getAttribute('content');
    const twitterImage = await page.locator('meta[name="twitter:image"]').getAttribute('content');
    
    expect(twitterCard).toBe('summary_large_image');
    expect(twitterTitle).toBeTruthy();
    expect(twitterImage).toMatch(/\/api\/og\/free-categorizer/);
  });
});

test.describe('Free Categorizer - JSON-LD Structured Data', () => {
  test('should have SoftwareApplication schema', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const scripts = await page.locator('script[type="application/ld+json"]').all();
    const scriptContents = await Promise.all(scripts.map(s => s.textContent()));
    
    const appSchema = scriptContents.find(content => content?.includes('SoftwareApplication'));
    expect(appSchema).toBeTruthy();
    
    const parsed = JSON.parse(appSchema!);
    expect(parsed['@type']).toBe('SoftwareApplication');
    expect(parsed.name).toContain('Free Bank Transaction Categorizer');
    expect(parsed.applicationCategory).toBe('FinanceApplication');
    expect(parsed.offers.price).toBe('0');
  });

  test('should have FAQPage schema', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const scripts = await page.locator('script[type="application/ld+json"]').all();
    const scriptContents = await Promise.all(scripts.map(s => s.textContent()));
    
    const faqSchema = scriptContents.find(content => content?.includes('FAQPage'));
    expect(faqSchema).toBeTruthy();
    
    const parsed = JSON.parse(faqSchema!);
    expect(parsed['@type']).toBe('FAQPage');
    expect(parsed.mainEntity).toHaveLength(5);
    expect(parsed.mainEntity[0].name).toBe('Is this safe?');
  });

  test('should have BreadcrumbList schema', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const scripts = await page.locator('script[type="application/ld+json"]').all();
    const scriptContents = await Promise.all(scripts.map(s => s.textContent()));
    
    const breadcrumbSchema = scriptContents.find(content => content?.includes('BreadcrumbList'));
    expect(breadcrumbSchema).toBeTruthy();
    
    const parsed = JSON.parse(breadcrumbSchema!);
    expect(parsed['@type']).toBe('BreadcrumbList');
    expect(parsed.itemListElement).toHaveLength(3);
    expect(parsed.itemListElement[2].name).toBe('Free Categorizer');
  });
});

test.describe('Free Categorizer - UX Elements', () => {
  test('should show H1 with correct text', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    const h1 = await page.locator('h1').textContent();
    expect(h1).toContain('Free Bank Transaction Categorizer');
    expect(h1).toContain('CSV');
    expect(h1).toContain('OFX');
    expect(h1).toContain('QFX');
  });

  test('should show consent toggle, sample buttons on first paint', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    // Consent toggle
    const consentCheckbox = page.locator('text=Allow anonymized data to improve models');
    await expect(consentCheckbox).toBeVisible();
    
    // Sample buttons
    const sampleBtn = page.locator('text=Use Sample Statement');
    await expect(sampleBtn).toBeVisible();
    
    const outputBtn = page.locator('text=See Sample CSV Output');
    await expect(outputBtn).toBeVisible();
  });

  test('should show trust strip', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    await expect(page.locator('text=Uploads deleted within 24 hours')).toBeVisible();
    await expect(page.locator('text=Opt-in training only')).toBeVisible();
    await expect(page.locator('text=SOC 2-aligned controls')).toBeVisible();
  });

  test('should show rich content section with FAQs', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    // Scroll to bottom to ensure content loads
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    await expect(page.locator('h2:has-text("How it works")')).toBeVisible();
    await expect(page.locator('h2:has-text("Supported formats")')).toBeVisible();
    await expect(page.locator('h2:has-text("Why this tool")')).toBeVisible();
    await expect(page.locator('h2:has-text("Frequently Asked Questions")')).toBeVisible();
  });

  test('should have internal links', async ({ page }) => {
    await page.goto(CATEGORIZER_URL);
    
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    await expect(page.locator('a[href="/pricing"]')).toHaveCount(3); // At least 3 pricing links
    await expect(page.locator('a[href="/privacy"]')).toBeVisible();
    await expect(page.locator('a[href="/security"]')).toBeVisible();
    await expect(page.locator('a[href="/dpa"]')).toBeVisible();
  });
});

test.describe('Free Categorizer - OG Image', () => {
  test('should return 200 for OG image endpoint', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/og/free-categorizer`);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('image/png');
  });
});

test.describe('Free Categorizer - Sitemap & Robots', () => {
  test('should include /free/categorizer in sitemap', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/sitemap.xml`);
    const text = await response.text();
    
    expect(text).toContain('/free/categorizer');
  });

  test('should allow /free/categorizer in robots.txt', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/robots.txt`);
    const text = await response.text();
    
    expect(text).not.toContain('Disallow: /free/categorizer');
    expect(text).toContain('Disallow: /setup');
  });

  test('should have noindex on /setup page', async ({ page }) => {
    await page.goto(`${BASE_URL}/setup`);
    
    const robots = await page.locator('meta[name="robots"]').getAttribute('content');
    expect(robots).toContain('noindex');
  });
});

