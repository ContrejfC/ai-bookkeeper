#!/usr/bin/env ts-node
/**
 * Sitemap Ping to Google
 * ======================
 * 
 * Notifies Google Search Console of sitemap updates.
 * Safe no-op if SITEMAP_URL not configured.
 * 
 * Usage:
 *   SITEMAP_URL=https://ai-bookkeeper.app/sitemap.xml npx ts-node scripts/ping-sitemap.ts
 */

async function main() {
  const sitemapUrl = process.env.SITEMAP_URL;
  
  if (!sitemapUrl) {
    console.log('ℹ️  SITEMAP_URL not set - skipping Google sitemap ping');
    process.exit(0);
  }
  
  const pingUrl = `https://www.google.com/ping?sitemap=${encodeURIComponent(sitemapUrl)}`;
  
  console.log(`📡 Pinging Google with sitemap: ${sitemapUrl}`);
  
  try {
    const response = await fetch(pingUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'AI-Bookkeeper-Sitemap-Ping/1.0'
      }
    });
    
    if (response.ok) {
      console.log(`✅ Sitemap ping successful (${response.status})`);
      console.log(`   Google has been notified of sitemap updates`);
      process.exit(0);
    } else {
      console.warn(`⚠️  Sitemap ping returned ${response.status}`);
      console.warn(`   This is not critical - Google will discover updates naturally`);
      
      // Don't fail in non-production
      if (process.env.NODE_ENV === 'production') {
        process.exit(1);
      } else {
        process.exit(0);
      }
    }
  } catch (error) {
    console.warn(`⚠️  Sitemap ping failed:`, error);
    console.warn(`   This is not critical - Google will discover updates naturally`);
    
    // Don't fail in non-production
    if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    } else {
      process.exit(0);
    }
  }
}

main();

