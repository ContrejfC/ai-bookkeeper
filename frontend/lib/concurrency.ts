/**
 * Per-IP Concurrency Gate
 * ========================
 * 
 * Limits concurrent requests per IP address to prevent DoS.
 * Uses Upstash Redis if configured, otherwise in-memory Map.
 * 
 * Example usage:
 * ```typescript
 * const ip = getClientIP(request);
 * const acquired = await acquireLock(ip, 2, 30000);
 * if (!acquired) {
 *   return NextResponse.json(
 *     { code: "CONCURRENCY_LIMIT", retryAfterSec: 5 },
 *     { status: 429 }
 *   );
 * }
 * try {
 *   // Process request
 * } finally {
 *   await releaseLock(ip);
 * }
 * ```
 */

// In-memory fallback (single-instance only, not for distributed)
const inMemoryLocks = new Map<string, { count: number; expiresAt: number }>();

// Cleanup expired locks every minute
setInterval(() => {
  const now = Date.now();
  for (const [key, value] of inMemoryLocks.entries()) {
    if (value.expiresAt < now) {
      inMemoryLocks.delete(key);
    }
  }
}, 60000);

/**
 * Get Upstash Redis client if configured
 */
function getRedisClient() {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  
  if (!url || !token) {
    return null;
  }
  
  // Use Upstash REST API directly (no SDK needed)
  return {
    url,
    token,
    async get(key: string): Promise<string | null> {
      const res = await fetch(`${url}/get/${key}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      return data.result;
    },
    async incr(key: string): Promise<number> {
      const res = await fetch(`${url}/incr/${key}`, {
        headers: { Authorization: `Bearer ${token}` },
        method: 'POST'
      });
      const data = await res.json();
      return data.result;
    },
    async decr(key: string): Promise<number> {
      const res = await fetch(`${url}/decr/${key}`, {
        headers: { Authorization: `Bearer ${token}` },
        method: 'POST'
      });
      const data = await res.json();
      return data.result;
    },
    async expire(key: string, seconds: number): Promise<void> {
      await fetch(`${url}/expire/${key}/${seconds}`, {
        headers: { Authorization: `Bearer ${token}` },
        method: 'POST'
      });
    }
  };
}

/**
 * Acquire a concurrency lock for an IP address
 * 
 * @param ip - Client IP address (hashed)
 * @param limit - Maximum concurrent requests per IP
 * @param ttlMs - Lock TTL in milliseconds (auto-release)
 * @returns True if lock acquired, false if limit exceeded
 */
export async function acquireLock(
  ip: string,
  limit: number = 2,
  ttlMs: number = 30000
): Promise<boolean> {
  const redis = getRedisClient();
  const key = `concurrency:${ip}`;
  
  if (redis) {
    // Use Upstash Redis
    try {
      const current = await redis.incr(key);
      await redis.expire(key, Math.ceil(ttlMs / 1000));
      
      if (current > limit) {
        // Exceeded limit, decrement back
        await redis.decr(key);
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('[Concurrency] Redis error, allowing request:', error);
      return true; // Fail open on Redis errors
    }
  } else {
    // In-memory fallback
    const now = Date.now();
    const existing = inMemoryLocks.get(key);
    
    // Clean up if expired
    if (existing && existing.expiresAt < now) {
      inMemoryLocks.delete(key);
    }
    
    const current = inMemoryLocks.get(key);
    
    if (current && current.count >= limit) {
      return false; // Limit exceeded
    }
    
    // Increment counter
    inMemoryLocks.set(key, {
      count: (current?.count || 0) + 1,
      expiresAt: now + ttlMs
    });
    
    return true;
  }
}

/**
 * Release a concurrency lock for an IP address
 * 
 * @param ip - Client IP address (hashed)
 */
export async function releaseLock(ip: string): Promise<void> {
  const redis = getRedisClient();
  const key = `concurrency:${ip}`;
  
  if (redis) {
    // Use Upstash Redis
    try {
      await redis.decr(key);
    } catch (error) {
      console.error('[Concurrency] Redis release error:', error);
    }
  } else {
    // In-memory fallback
    const existing = inMemoryLocks.get(key);
    
    if (existing) {
      if (existing.count <= 1) {
        inMemoryLocks.delete(key);
      } else {
        existing.count--;
      }
    }
  }
}

/**
 * Get current concurrency count for an IP
 * 
 * @param ip - Client IP address (hashed)
 * @returns Current count
 */
export async function getConcurrencyCount(ip: string): Promise<number> {
  const redis = getRedisClient();
  const key = `concurrency:${ip}`;
  
  if (redis) {
    try {
      const value = await redis.get(key);
      return value ? parseInt(value, 10) : 0;
    } catch (error) {
      return 0;
    }
  } else {
    const now = Date.now();
    const existing = inMemoryLocks.get(key);
    
    if (!existing || existing.expiresAt < now) {
      return 0;
    }
    
    return existing.count;
  }
}

/**
 * Extract client IP from request
 * Checks X-Forwarded-For, X-Real-IP, then connection
 * 
 * @param request - Next.js request object
 * @returns IP address string
 */
export function getClientIP(request: Request): string {
  const headers = request.headers;
  
  // Check X-Forwarded-For (Vercel/Cloudflare)
  const forwarded = headers.get('x-forwarded-for');
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  
  // Check X-Real-IP
  const realIP = headers.get('x-real-ip');
  if (realIP) {
    return realIP;
  }
  
  // Fallback
  return 'unknown';
}

/**
 * Hash IP for privacy (optional)
 * 
 * @param ip - Raw IP address
 * @returns Hashed IP
 */
export async function hashIP(ip: string): Promise<string> {
  const salt = process.env.IP_HASH_SALT || 'default-salt-change-in-production';
  const encoder = new TextEncoder();
  const data = encoder.encode(ip + salt);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16);
}

