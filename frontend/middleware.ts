/**
 * Canonical Domain Middleware
 * ============================
 * 
 * Redirects all requests to the canonical domain (ai-bookkeeper.app).
 * Uses 308 (Permanent Redirect) to preserve HTTP method and ensure
 * search engines understand the canonical URL.
 * 
 * Redirects:
 * - *.vercel.app → ai-bookkeeper.app
 * - Any other host → ai-bookkeeper.app
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getClientIP, hashIP } from "./lib/concurrency";

const CANONICAL_HOST = "ai-bookkeeper.app";

// Rate limiting state (in-memory, per-instance)
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

// Cleanup expired rate limit entries every minute
setInterval(() => {
  const now = Date.now();
  for (const [key, value] of rateLimitMap.entries()) {
    if (value.resetAt < now) {
      rateLimitMap.delete(key);
    }
  }
}, 60000);

export async function middleware(req: NextRequest) {
  const host = req.headers.get("host");
  const pathname = req.nextUrl.pathname;
  
  // If host doesn't match canonical, redirect with 308
  if (host && host !== CANONICAL_HOST) {
    const url = new URL(req.url);
    url.protocol = "https:";
    url.host = CANONICAL_HOST;
    
    // 308 Permanent Redirect preserves the HTTP method
    return NextResponse.redirect(url, 308);
  }
  
  // Rate limiting for /api/free/categorizer/* paths
  if (pathname.startsWith('/api/free/categorizer/')) {
    const rateLimit = await checkRateLimit(req);
    
    if (!rateLimit.allowed) {
      return NextResponse.json(
        {
          code: "RATE_LIMIT_EXCEEDED",
          message: "Too many requests. Please try again later.",
          retryAfterSec: Math.ceil((rateLimit.resetAt - Date.now()) / 1000)
        },
        {
          status: 429,
          headers: {
            "Retry-After": String(Math.ceil((rateLimit.resetAt - Date.now()) / 1000)),
            "X-RateLimit-Limit": "20",
            "X-RateLimit-Remaining": String(Math.max(0, 20 - rateLimit.count))
          }
        }
      );
    }
  }
  
  // Add security headers
  const response = NextResponse.next();
  
  // Content Security Policy
  response.headers.set(
    "Content-Security-Policy",
    "default-src 'self'; " +
    "img-src 'self' data: blob:; " +
    "style-src 'self' 'unsafe-inline'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "connect-src 'self' https://api.openai.com https://api.ai-bookkeeper.app; " +
    "frame-ancestors 'none'"
  );
  
  // Security headers
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=()"
  );
  
  // HSTS (HTTP Strict Transport Security)
  response.headers.set(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains"
  );
  
  return response;
}

/**
 * Check rate limit for a request
 * 
 * @param req - Next.js request
 * @returns allowed: boolean, count: number, resetAt: timestamp
 */
async function checkRateLimit(req: NextRequest): Promise<{
  allowed: boolean;
  count: number;
  resetAt: number;
}> {
  const limit = 20; // 20 requests per minute
  const windowMs = 60000; // 1 minute
  
  const ip = getClientIP(req);
  const ipHash = await hashIP(ip);
  const key = `ratelimit:${ipHash}`;
  const now = Date.now();
  
  // Check if Upstash is configured
  const hasUpstash = process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN;
  
  if (!hasUpstash) {
    // No rate limiting configured, just log
    console.log(`[RateLimit] No Upstash configured, allowing request from ${ipHash}`);
    return { allowed: true, count: 0, resetAt: now + windowMs };
  }
  
  // Use in-memory rate limiting
  let entry = rateLimitMap.get(key);
  
  if (!entry || entry.resetAt < now) {
    // New window
    entry = {
      count: 1,
      resetAt: now + windowMs
    };
    rateLimitMap.set(key, entry);
    return { allowed: true, count: 1, resetAt: entry.resetAt };
  }
  
  // Increment count
  entry.count++;
  
  if (entry.count > limit) {
    return { allowed: false, count: entry.count, resetAt: entry.resetAt };
  }
  
  return { allowed: true, count: entry.count, resetAt: entry.resetAt };
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico (favicon)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};

