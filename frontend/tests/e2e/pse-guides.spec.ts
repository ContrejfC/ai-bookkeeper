/**
 * PSE Guides E2E Tests
 * =====================
 * 
 * Tests for programmatic SEO bank export guide pages.
 * Validates SEO metadata, JSON-LD, CTAs, OG images, and noindex handling.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

// Test sample banks
const ACTIVE_BANKS = [
  { slug: 'chase-export-csv', name: 'Chase' },
  { slug: 'bank-of-america-export-csv', name: 'Bank of America' },
  { slug: 'american-express-business-export-csv', name: 'American Express Business' },
];

const NOINDEX_BANK = {
  slug: 'peoples-united-export-csv',
  name: "People's United Bank",
};

test.describe('PSE Bank Export Guides', () => {
  for (const bank of ACTIVE_BANKS) {
    test.describe(`${bank.name} guide (${bank.slug})`, () => {
      test('should return 200 status', async ({ page }) => {
        const response = await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        expect(response?.status()).toBe(200);
      });

      test('should have correct H1 with bank name', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const h1 = await page.locator('h1').first();
        await expect(h1).toBeVisible();
        const h1Text = await h1.textContent();
        expect(h1Text).toContain(bank.name);
        expect(h1Text).toContain('export');
        expect(h1Text).toContain('CSV');
      });

      test('should have canonical link pointing to ai-bookkeeper.app', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const canonical = await page.locator('link[rel="canonical"]');
        await expect(canonical).toHaveAttribute('href', `https://ai-bookkeeper.app/guides/${bank.slug}`);
      });

      test('should have robots meta tag allowing indexing', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        // Check that noindex is NOT present (active banks should be indexed)
        const noindexMeta = await page.locator('meta[name="robots"][content*="noindex"]').count();
        expect(noindexMeta).toBe(0);
        
        // Verify robots header allows indexing
        const robotsHeader = await page.locator('meta[name="robots"]').first();
        if (await robotsHeader.count() > 0) {
          const content = await robotsHeader.getAttribute('content');
          expect(content).not.toContain('noindex');
        }
      });

      test('should include HowTo JSON-LD schema', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const jsonLdScripts = await page.locator('script[type="application/ld+json"]').all();
        
        // Should have at least 2 JSON-LD schemas
        expect(jsonLdScripts.length).toBeGreaterThanOrEqual(2);
        
        let foundHowTo = false;
        for (const script of jsonLdScripts) {
          const content = await script.textContent();
          if (content) {
            const json = JSON.parse(content);
            if (json['@type'] === 'HowTo') {
              foundHowTo = true;
              expect(json.step).toBeDefined();
              expect(json.step.length).toBeGreaterThanOrEqual(4);
              break;
            }
          }
        }
        expect(foundHowTo).toBe(true);
      });

      test('should include FAQPage JSON-LD schema', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const jsonLdScripts = await page.locator('script[type="application/ld+json"]').all();
        
        let foundFAQ = false;
        for (const script of jsonLdScripts) {
          const content = await script.textContent();
          if (content) {
            const json = JSON.parse(content);
            if (json['@type'] === 'FAQPage') {
              foundFAQ = true;
              expect(json.mainEntity).toBeDefined();
              expect(json.mainEntity.length).toBeGreaterThan(0);
              break;
            }
          }
        }
        expect(foundFAQ).toBe(true);
      });

      test('should include BreadcrumbList JSON-LD schema', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const jsonLdScripts = await page.locator('script[type="application/ld+json"]').all();
        
        let foundBreadcrumb = false;
        for (const script of jsonLdScripts) {
          const content = await script.textContent();
          if (content) {
            const json = JSON.parse(content);
            if (json['@type'] === 'BreadcrumbList') {
              foundBreadcrumb = true;
              expect(json.itemListElement).toBeDefined();
              expect(json.itemListElement.length).toBeGreaterThanOrEqual(3);
              break;
            }
          }
        }
        expect(foundBreadcrumb).toBe(true);
      });

      test('should have "Use Free Categorizer" CTA linking to /free/categorizer', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const ctaLink = await page.locator('a[href="/free/categorizer"]').first();
        await expect(ctaLink).toBeVisible();
        const ctaText = await ctaLink.textContent();
        expect(ctaText?.toLowerCase()).toContain('categorizer');
      });

      test('should have "See pricing" CTA linking to /pricing', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const pricingLink = await page.locator('a[href="/pricing"]').first();
        await expect(pricingLink).toBeVisible();
      });

      test('should have non-affiliation disclaimer visible', async ({ page }) => {
        await page.goto(`${BASE_URL}/guides/${bank.slug}`);
        const disclaimer = await page.getByText(/not affiliated with/i);
        await expect(disclaimer).toBeVisible();
      });

      test('OG image endpoint should return 200 with cache headers', async ({ request }) => {
        const response = await request.get(`${BASE_URL}/api/og/pse?slug=${bank.slug}`);
        expect(response.status()).toBe(200);
        expect(response.headers()['content-type']).toContain('image/png');
        
        // Check cache headers
        const cacheControl = response.headers()['cache-control'];
        expect(cacheControl).toContain('public');
        expect(cacheControl).toContain('max-age=86400');
      });
    });
  }

  test.describe('Noindex bank page', () => {
    test('should render with noindex meta tag', async ({ page }) => {
      const response = await page.goto(`${BASE_URL}/guides/${NOINDEX_BANK.slug}`);
      expect(response?.status()).toBe(200);

      // Should have noindex robots meta
      const robotsMeta = await page.locator('meta[name="robots"]');
      await expect(robotsMeta).toHaveAttribute('content', /noindex/);
    });

    test('should have H1 with bank name', async ({ page }) => {
      await page.goto(`${BASE_URL}/guides/${NOINDEX_BANK.slug}`);
      const h1 = await page.locator('h1').first();
      await expect(h1).toBeVisible();
      const h1Text = await h1.textContent();
      expect(h1Text).toContain(NOINDEX_BANK.name);
    });

    test('should NOT be included in sitemap', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/sitemap.xml`);
      expect(response.status()).toBe(200);
      const sitemap = await response.text();
      
      // Noindex banks should not appear in sitemap
      expect(sitemap).not.toContain(NOINDEX_BANK.slug);
    });
  });

  test.describe('Invalid bank slug', () => {
    test('should return 404 for non-existent bank', async ({ page }) => {
      const response = await page.goto(`${BASE_URL}/guides/not-a-real-bank-export-csv`, {
        waitUntil: 'domcontentloaded',
      });
      expect(response?.status()).toBe(404);
    });
  });

  test.describe('Sitemap integration', () => {
    test('should include active guide pages in sitemap', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/sitemap.xml`);
      expect(response.status()).toBe(200);
      const sitemap = await response.text();
      
      // Check that active banks are in sitemap
      for (const bank of ACTIVE_BANKS) {
        expect(sitemap).toContain(`/guides/${bank.slug}`);
      }
    });

    test('should have ≥50 guide URLs in sitemap', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/sitemap.xml`);
      const sitemap = await response.text();
      
      // Count guide URLs
      const guideMatches = sitemap.match(/\/guides\/[^<]+/g) || [];
      const guideCount = guideMatches.length;
      
      expect(guideCount).toBeGreaterThanOrEqual(50);
    });

    test('should have proper sitemap structure with loc and lastmod', async ({ request }) => {
      const response = await request.get(`${BASE_URL}/sitemap.xml`);
      const sitemap = await response.text();
      
      // Should be valid XML with urlset
      expect(sitemap).toContain('<urlset');
      expect(sitemap).toContain('</urlset>');
      
      // Should have loc tags for guide pages
      expect(sitemap).toMatch(/<loc>.*\/guides\//);
      
      // Should have lastmod tags
      expect(sitemap).toContain('<lastmod>');
    });
  });

  test.describe('Performance and accessibility', () => {
    test('should load page in reasonable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto(`${BASE_URL}/guides/${ACTIVE_BANKS[0].slug}`, {
        waitUntil: 'networkidle',
      });
      const loadTime = Date.now() - startTime;
      
      // Should load in under 3 seconds (LCP target)
      expect(loadTime).toBeLessThan(3000);
    });

    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto(`${BASE_URL}/guides/${ACTIVE_BANKS[0].slug}`);
      
      // Should have exactly one H1
      const h1Count = await page.locator('h1').count();
      expect(h1Count).toBe(1);
      
      // Should have H2s for sections
      const h2Count = await page.locator('h2').count();
      expect(h2Count).toBeGreaterThan(2);
    });

    test('should have accessible links with proper labels', async ({ page }) => {
      await page.goto(`${BASE_URL}/guides/${ACTIVE_BANKS[0].slug}`);
      
      // All links should have accessible text
      const links = await page.locator('a').all();
      for (const link of links) {
        const text = await link.textContent();
        const ariaLabel = await link.getAttribute('aria-label');
        expect(text || ariaLabel).toBeTruthy();
      }
    });
  });
});

