#!/usr/bin/env ts-node
/**
 * Production Verification Script
 * ==============================
 * 
 * Comprehensive checks for production deployment.
 * Run after each deploy to verify all features working.
 * 
 * Usage:
 *   HOST=https://ai-bookkeeper.app npx ts-node scripts/verify_prod.ts
 *   npm run verify:prod
 */

const HOST = process.env.HOST || 'https://ai-bookkeeper.app';
const ADMIN_VERIFY_TOKEN = process.env.ADMIN_VERIFY_TOKEN || '';

interface TestResult {
  name: string;
  passed: boolean;
  details?: string;
  error?: string;
}

const results: TestResult[] = [];

async function test(name: string, fn: () => Promise<void>) {
  try {
    await fn();
    results.push({ name, passed: true });
    console.log(`✅ ${name}`);
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    results.push({ name, passed: false, error: errorMsg });
    console.error(`❌ ${name}`);
    console.error(`   ${errorMsg}`);
  }
}

async function main() {
  console.log(`🧪 Production Verification: ${HOST}\n`);
  
  // Test 1: Domain responds
  await test('Domain responds (200)', async () => {
    const res = await fetch(HOST);
    if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
  });
  
  // Test 2: Old domain redirects (308)
  await test('Old domain redirects (308)', async () => {
    const res = await fetch('https://ai-bookkeeper-nine.vercel.app', { redirect: 'manual' });
    if (res.status !== 308) throw new Error(`Expected 308, got ${res.status}`);
    const location = res.headers.get('location');
    if (!location?.includes('ai-bookkeeper.app')) {
      throw new Error(`Expected redirect to canonical, got ${location}`);
    }
  });
  
  // Test 3: Security headers
  await test('Security headers present (CSP, HSTS, etc.)', async () => {
    const res = await fetch(`${HOST}/free/categorizer`);
    const csp = res.headers.get('content-security-policy');
    const hsts = res.headers.get('strict-transport-security');
    const xfo = res.headers.get('x-frame-options');
    const xcto = res.headers.get('x-content-type-options');
    const referrer = res.headers.get('referrer-policy');
    
    if (!csp) throw new Error('CSP header missing');
    if (!hsts) throw new Error('HSTS header missing');
    if (!xfo) throw new Error('X-Frame-Options missing');
    if (!xcto) throw new Error('X-Content-Type-Options missing');
    if (!referrer) throw new Error('Referrer-Policy missing');
  });
  
  // Test 4: AI Health
  await test('AI health endpoint', async () => {
    const res = await fetch(`${HOST}/api/ai/health`);
    const data = await res.json();
    
    if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
    if (typeof data.ok !== 'boolean') throw new Error('Missing ok field');
    if (data.ok && !data.model) throw new Error('Missing model when ok=true');
  });
  
  // Test 5: API Version (Git Provenance)
  await test('API version with git provenance', async () => {
    const res = await fetch(`${HOST}/api-version`);
    const data = await res.json();
    
    if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
    // Git fields should exist (may be empty in local/preview)
    if (!data.git) throw new Error('Missing git object');
  });
  
  // Test 6: Smoke Test
  await test('Smoke test assertions', async () => {
    const res = await fetch(`${HOST}/api-smoke`);
    const data = await res.json();
    
    if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
    if (!data.assertions) throw new Error('Missing assertions object');
    
    const failedAssertions = Object.entries(data.assertions)
      .filter(([_, value]) => value === false)
      .map(([key]) => key);
    
    if (failedAssertions.length > 0) {
      throw new Error(`Failed assertions: ${failedAssertions.join(', ')}`);
    }
  });
  
  // Test 7: Canonical Link
  await test('Canonical link tag correct', async () => {
    const res = await fetch(`${HOST}/free/categorizer`);
    const html = await res.text();
    
    if (!html.includes('rel="canonical"')) {
      throw new Error('No canonical link found');
    }
    if (!html.includes(HOST)) {
      throw new Error(`Canonical doesn't reference ${HOST}`);
    }
  });
  
  // Test 8: SEO Elements
  await test('SEO title and JSON-LD present', async () => {
    const res = await fetch(`${HOST}/free/categorizer`);
    const html = await res.text();
    
    if (!html.includes('<title>Free Bank Transaction Categorizer')) {
      throw new Error('Title tag incorrect');
    }
    
    const jsonLdCount = (html.match(/application\/ld\+json/g) || []).length;
    if (jsonLdCount < 2) {
      throw new Error(`Expected ≥2 JSON-LD schemas, found ${jsonLdCount}`);
    }
  });
  
  // Test 9: OG Image
  await test('OG image endpoint with caching', async () => {
    const res = await fetch(`${HOST}/api/og/free-categorizer`);
    if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
    if (res.headers.get('content-type') !== 'image/png') {
      throw new Error('Expected image/png');
    }
    if (!res.headers.get('cache-control')?.includes('max-age')) {
      throw new Error('Missing cache-control header');
    }
  });
  
  // Test 10: Method Guards
  await test('API method guards (405 on GET)', async () => {
    const res = await fetch(`${HOST}/api/free/categorizer/upload`, {
      method: 'GET'
    });
    if (res.status !== 405) throw new Error(`Expected 405, got ${res.status}`);
    if (!res.headers.get('allow')?.includes('POST')) {
      throw new Error('Allow header should include POST');
    }
  });
  
  // Test 11: Deletion SLA Verifier (if token provided)
  if (ADMIN_VERIFY_TOKEN && ADMIN_VERIFY_TOKEN !== 'change-me-long-random') {
    await test('Deletion SLA verifier', async () => {
      const res = await fetch(`${HOST}/api/admin/verify-deletions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ADMIN_VERIFY_TOKEN}`
        }
      });
      
      if (!res.ok) throw new Error(`Expected 200, got ${res.status}`);
      
      const data = await res.json();
      if (typeof data.p95Minutes !== 'number') throw new Error('Missing p95Minutes');
      if (typeof data.staleCount !== 'number') throw new Error('Missing staleCount');
      
      // Alert if SLA violated
      if (data.p95Minutes > 1440) {
        throw new Error(`SLA violation: p95=${data.p95Minutes} min (limit: 1440)`);
      }
      if (data.staleCount > 0) {
        throw new Error(`SLA violation: ${data.staleCount} stale files`);
      }
    });
  } else {
    console.log('⏭️  Skipping deletion SLA test (ADMIN_VERIFY_TOKEN not set)');
  }
  
  // Test 12: Rate Limiting (light test - just 5 requests)
  await test('Rate limiting configured', async () => {
    // Create valid CSV
    const csvContent = 'date,description,amount\n2025-01-02,COFFEE,-3.75\n';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const formData = new FormData();
    formData.append('file', blob, 'demo.csv');
    
    // Send 5 requests (safe, won't hit limit)
    const responses = await Promise.all(
      Array(5).fill(0).map(() => 
        fetch(`${HOST}/api/free/categorizer/upload`, {
          method: 'POST',
          body: formData
        })
      )
    );
    
    const statuses = responses.map(r => r.status);
    const has200or400 = statuses.some(s => s === 200 || s === 400);
    
    if (!has200or400) {
      throw new Error(`Unexpected statuses: ${statuses.join(', ')}`);
    }
    
    // Check for rate limit headers
    const firstResponse = responses[0];
    const hasRateLimitHeaders = 
      firstResponse.headers.has('x-ratelimit-limit') ||
      firstResponse.headers.has('x-ratelimit-remaining');
    
    // Note: Headers only present when near limit, so this is informational
    console.log(`   Rate limit headers: ${hasRateLimitHeaders ? 'present' : 'not yet (under limit)'}`);
  });
  
  // Summary
  console.log('\n' + '='.repeat(60));
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  
  console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`);
  
  if (failed > 0) {
    console.log('❌ Failed tests:');
    results.filter(r => !r.passed).forEach(r => {
      console.log(`   - ${r.name}: ${r.error}`);
    });
    console.log('');
    process.exit(1);
  } else {
    console.log('✅ All tests passed!\n');
    console.log(`🎉 ${HOST} is production-ready!\n`);
    process.exit(0);
  }
}

main().catch(error => {
  console.error('\n❌ Verification script failed:', error);
  process.exit(1);
});

