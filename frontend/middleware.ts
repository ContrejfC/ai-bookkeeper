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

const CANONICAL_HOST = "ai-bookkeeper.app";

export function middleware(req: NextRequest) {
  const host = req.headers.get("host");
  
  // If host doesn't match canonical, redirect with 308
  if (host && host !== CANONICAL_HOST) {
    const url = new URL(req.url);
    url.protocol = "https:";
    url.host = CANONICAL_HOST;
    
    // 308 Permanent Redirect preserves the HTTP method
    return NextResponse.redirect(url, 308);
  }
  
  // Add security headers
  const response = NextResponse.next();
  
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

