/**
 * Runtime Smoke Test Endpoint
 * ===========================
 * 
 * Server-side checks for key pages and API routes.
 * Validates:
 * - Policy dates (November 3, 2025)
 * - SOC2 copy
 * - API route 405 guards
 * - UI controls presence
 */

import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

async function fetchTxt(path: string, init?: RequestInit) {
  const res = await fetch(path, { ...init, cache: 'no-store' });
  const text = await res.text();
  return { 
    status: res.status, 
    ok: res.ok, 
    headers: Object.fromEntries(res.headers.entries()), 
    text 
  };
}

export async function GET(req: NextRequest) {
  const base = `${req.nextUrl.protocol}//${req.headers.get('host')}`;
  const checks: Record<string, any> = {};

  try {
    // 1) Policy dates
    checks.privacy = await fetchTxt(`${base}/privacy`);
    checks.terms = await fetchTxt(`${base}/terms`);
    const dateOk = (html: string) => /November 3, 2025/.test(html);

    // 2) SOC2 wording
    checks.security = await fetchTxt(`${base}/security`);
    const socOk = /SOC 2-aligned controls|SOC 2 Type II (certified|in progress)/i.test(checks.security.text);

    // 3) API route presence via method guard
    const resUploadGet = await fetch(`${base}/api/free/categorizer/upload`, { 
      method: 'GET',
      cache: 'no-store'
    });
    checks.apiUploadGET = { 
      status: resUploadGet.status, 
      allow: resUploadGet.headers.get('allow') 
    };

    // 4) UI strings existence (SSR HTML)
    checks.free = await fetchTxt(`${base}/free/categorizer`);
    const uiOk = /(Allow anonymized data to improve models \(optional\))|Use Sample Statement|See Sample CSV Output/.test(checks.free.text);

    // Build result
    const result = {
      base,
      timestamp: new Date().toISOString(),
      assertions: {
        privacyDate: dateOk(checks.privacy.text),
        termsDate: dateOk(checks.terms.text),
        soc2Copy: socOk,
        apiUpload405: checks.apiUploadGET.status === 405 && (checks.apiUploadGET.allow ?? '').includes('POST'),
        uiControls: uiOk,
      },
      raw: {
        privacyStatus: checks.privacy.status,
        termsStatus: checks.terms.status,
        securityStatus: checks.security.status,
        freeStatus: checks.free.status,
        apiUploadGET: checks.apiUploadGET,
      }
    };

    const ok = Object.values(result.assertions).every(Boolean);
    
    return new Response(JSON.stringify(result, null, 2), {
      status: ok ? 200 : 500,
      headers: { 'content-type': 'application/json; charset=utf-8' },
    });
    
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Smoke test failed',
      message: error instanceof Error ? error.message : String(error),
      timestamp: new Date().toISOString()
    }, null, 2), {
      status: 500,
      headers: { 'content-type': 'application/json; charset=utf-8' },
    });
  }
}

