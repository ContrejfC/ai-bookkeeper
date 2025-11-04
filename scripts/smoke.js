#!/usr/bin/env node
/**
 * Production Smoke Test Script
 * ============================
 * 
 * Validates production deployment by checking:
 * - Policy dates
 * - SOC2 copy
 * - API route guards
 * - UI controls presence
 * 
 * Usage:
 *   HOST=https://ai-bookkeeper-nine.vercel.app node scripts/smoke.js
 *   npm run smoke:prod
 */

const https = require('https');

const host = process.env.HOST || 'https://ai-bookkeeper-nine.vercel.app';

function curl(path, method = 'GET') {
  return fetch(host + path, { method })
    .then(r => r.text().then(t => ({
      status: r.status,
      headers: Object.fromEntries(r.headers),
      text: t
    })));
}

(async () => {
  console.log(`🧪 Running smoke tests against: ${host}\n`);
  
  try {
    // Fetch all pages and APIs
    // Use the /__smoke endpoint if available, otherwise run individual checks
    const smokeEndpoint = await fetch(host + '/api-smoke', { method: 'GET' });
    
    if (smokeEndpoint.ok) {
      // Use server-side smoke test
      const result = await smokeEndpoint.json();
      console.log(JSON.stringify(result, null, 2));
      
      const allOk = Object.values(result.assertions).every(Boolean);
      console.log('\n' + '='.repeat(50));
      console.log('SMOKE TEST SUMMARY');
      console.log('='.repeat(50));
      
      for (const [key, value] of Object.entries(result.assertions)) {
        const status = value ? '✅ PASS' : '❌ FAIL';
        console.log(`${status} - ${key}`);
      }
      
      console.log('='.repeat(50));
      console.log(`Overall: ${allOk ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
      console.log('='.repeat(50) + '\n');
      
      process.exit(allOk ? 0 : 1);
    }
    
    // Fallback: Run individual checks
    const privacy = await curl('/privacy');
    const terms = await curl('/terms');
    const security = await curl('/security');
    const apiGet = await fetch(host + '/api/free/categorizer/upload', { method: 'GET' });
    const free = await curl('/free/categorizer');
    
    // Run assertions
    const assertions = {
      privacyDate: /November 3, 2025/.test(privacy.text),
      termsDate: /November 3, 2025/.test(terms.text),
      soc2Copy: /SOC 2-aligned controls|SOC 2 Type II (certified|in progress)/i.test(security.text),
      apiUpload405: apiGet.status === 405 && (apiGet.headers.get('allow') || '').includes('POST'),
      uiControls: /(Allow anonymized data to improve models \(optional\))|Use Sample Statement|See Sample CSV Output/.test(free.text)
    };
    
    const allOk = Object.values(assertions).every(Boolean);
    
    // Build result
    const result = {
      host,
      timestamp: new Date().toISOString(),
      ok: allOk,
      assertions,
      statuses: {
        privacy: privacy.status,
        terms: terms.status,
        security: security.status,
        free: free.status,
        apiUploadGET: apiGet.status
      }
    };
    
    // Output
    console.log(JSON.stringify(result, null, 2));
    
    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('SMOKE TEST SUMMARY');
    console.log('='.repeat(50));
    
    for (const [key, value] of Object.entries(assertions)) {
      const status = value ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} - ${key}`);
    }
    
    console.log('='.repeat(50));
    console.log(`Overall: ${allOk ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
    console.log('='.repeat(50) + '\n');
    
    process.exit(allOk ? 0 : 1);
    
  } catch (error) {
    console.error('❌ Smoke test error:', error);
    process.exit(1);
  }
})();

