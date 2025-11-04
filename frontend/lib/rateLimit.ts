/**
 * Free Tool Rate Limiting
 * 
 * Implements token bucket rate limiting with Redis or in-memory fallback.
 * Prevents abuse of the free statement categorizer tool.
 */

import { Redis } from 'ioredis';
import { loadFreeToolConfig } from './config-server';

// Redis client (singleton)
let redisClient: Redis | null = null;

function getRedisClient(): Redis | null {
  if (redisClient) return redisClient;
  
  const redisUrl = process.env.RATE_LIMIT_REDIS_URL;
  
  if (!redisUrl) {
    return null; // Fall back to in-memory
  }
  
  try {
    redisClient = new Redis(redisUrl, {
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      lazyConnect: true
    });
    
    redisClient.on('error', (err) => {
      console.error('Redis error:', err);
    });
    
    return redisClient;
  } catch (error) {
    console.error('Failed to connect to Redis:', error);
    return null;
  }
}

// In-memory fallback (not suitable for multi-instance deployments)
class InMemoryRateLimiter {
  private buckets: Map<string, { tokens: number; lastRefill: number }>;
  
  constructor() {
    this.buckets = new Map();
    
    // Clean up old entries every 5 minutes
    setInterval(() => {
      const now = Date.now();
      for (const [key, bucket] of this.buckets.entries()) {
        if (now - bucket.lastRefill > 3600000) { // 1 hour
          this.buckets.delete(key);
        }
      }
    }, 300000);
  }
  
  async checkLimit(key: string, maxTokens: number, refillRatePerSecond: number): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: Date;
  }> {
    const now = Date.now();
    const bucket = this.buckets.get(key);
    
    if (!bucket) {
      // New bucket
      this.buckets.set(key, {
        tokens: maxTokens - 1,
        lastRefill: now
      });
      
      return {
        allowed: true,
        remaining: maxTokens - 1,
        resetAt: new Date(now + (3600000 / refillRatePerSecond))
      };
    }
    
    // Refill tokens
    const secondsElapsed = (now - bucket.lastRefill) / 1000;
    const tokensToAdd = Math.floor(secondsElapsed * refillRatePerSecond);
    
    if (tokensToAdd > 0) {
      bucket.tokens = Math.min(maxTokens, bucket.tokens + tokensToAdd);
      bucket.lastRefill = now;
    }
    
    // Check if request allowed
    if (bucket.tokens > 0) {
      bucket.tokens -= 1;
      this.buckets.set(key, bucket);
      
      return {
        allowed: true,
        remaining: bucket.tokens,
        resetAt: new Date(now + ((maxTokens - bucket.tokens) / refillRatePerSecond * 1000))
      };
    }
    
    return {
      allowed: false,
      remaining: 0,
      resetAt: new Date(now + (1 / refillRatePerSecond * 1000))
    };
  }
}

const inMemoryLimiter = new InMemoryRateLimiter();

/**
 * Check rate limit using token bucket algorithm
 */
async function checkRateLimitRedis(
  key: string,
  maxTokens: number,
  refillRatePerSecond: number
): Promise<{ allowed: boolean; remaining: number; resetAt: Date }> {
  const redis = getRedisClient();
  
  if (!redis) {
    // Fall back to in-memory
    return inMemoryLimiter.checkLimit(key, maxTokens, refillRatePerSecond);
  }
  
  const now = Date.now();
  const bucketKey = `rate_limit:${key}`;
  
  try {
    await redis.connect();
    
    // Get current bucket state
    const bucketData = await redis.get(bucketKey);
    
    if (!bucketData) {
      // New bucket
      await redis.set(bucketKey, JSON.stringify({
        tokens: maxTokens - 1,
        lastRefill: now
      }), 'EX', 3600); // Expire after 1 hour
      
      return {
        allowed: true,
        remaining: maxTokens - 1,
        resetAt: new Date(now + (3600000 / refillRatePerSecond))
      };
    }
    
    const bucket = JSON.parse(bucketData);
    
    // Refill tokens
    const secondsElapsed = (now - bucket.lastRefill) / 1000;
    const tokensToAdd = Math.floor(secondsElapsed * refillRatePerSecond);
    
    if (tokensToAdd > 0) {
      bucket.tokens = Math.min(maxTokens, bucket.tokens + tokensToAdd);
      bucket.lastRefill = now;
    }
    
    // Check if request allowed
    if (bucket.tokens > 0) {
      bucket.tokens -= 1;
      await redis.set(bucketKey, JSON.stringify(bucket), 'EX', 3600);
      
      return {
        allowed: true,
        remaining: bucket.tokens,
        resetAt: new Date(now + ((maxTokens - bucket.tokens) / refillRatePerSecond * 1000))
      };
    }
    
    return {
      allowed: false,
      remaining: 0,
      resetAt: new Date(now + (1 / refillRatePerSecond * 1000))
    };
  } catch (error) {
    console.error('Rate limit error:', error);
    // On error, allow request (fail open)
    return { allowed: true, remaining: maxTokens, resetAt: new Date() };
  }
}

/**
 * Check IP-based rate limit
 */
export async function checkIPRateLimit(ip: string): Promise<{
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}> {
  const config = loadFreeToolConfig();
  const maxPerHour = config.rate_limit?.ip_per_hour || 20;
  const refillRate = maxPerHour / 3600; // tokens per second
  
  return checkRateLimitRedis(`ip:${ip}`, maxPerHour, refillRate);
}

/**
 * Check email-based rate limit
 */
export async function checkEmailRateLimit(email: string): Promise<{
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}> {
  const config = loadFreeToolConfig();
  const maxPerDay = config.rate_limit?.email_per_day || 3;
  const refillRate = maxPerDay / 86400; // tokens per second
  
  // Hash email for key
  const emailHash = hashEmail(email);
  
  return checkRateLimitRedis(`email:${emailHash}`, maxPerDay, refillRate);
}

/**
 * Check global rate limit
 */
export async function checkGlobalRateLimit(): Promise<{
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}> {
  const config = loadFreeToolConfig();
  const maxPerMinute = config.rate_limit?.global_per_minute || 100;
  const refillRate = maxPerMinute / 60; // tokens per second
  
  return checkRateLimitRedis('global', maxPerMinute, refillRate);
}

/**
 * Check ban list
 */
export async function checkBanList(ip: string, email?: string): Promise<boolean> {
  const config = loadFreeToolConfig();
  
  if (!config.security?.ban_list_enabled) {
    return false; // Not banned
  }
  
  const redis = getRedisClient();
  
  if (!redis) {
    return false; // No ban list without Redis
  }
  
  try {
    await redis.connect();
    
    // Check IP ban
    const ipBanned = await redis.get(`ban:ip:${ip}`);
    if (ipBanned) return true;
    
    // Check email ban (if provided)
    if (email) {
      const emailHash = hashEmail(email);
      const emailBanned = await redis.get(`ban:email:${emailHash}`);
      if (emailBanned) return true;
    }
    
    return false;
  } catch (error) {
    console.error('Ban list check error:', error);
    return false; // On error, don't ban (fail open)
  }
}

/**
 * Add IP to ban list
 */
export async function banIP(ip: string, reason: string, durationSeconds: number = 86400): Promise<void> {
  const redis = getRedisClient();
  
  if (!redis) {
    console.warn('Cannot ban IP without Redis');
    return;
  }
  
  try {
    await redis.connect();
    await redis.set(`ban:ip:${ip}`, JSON.stringify({ reason, banned_at: new Date().toISOString() }), 'EX', durationSeconds);
    console.log(`Banned IP ${ip} for ${durationSeconds}s: ${reason}`);
  } catch (error) {
    console.error('Failed to ban IP:', error);
  }
}

/**
 * Add email to ban list
 */
export async function banEmail(email: string, reason: string, durationSeconds: number = 86400): Promise<void> {
  const redis = getRedisClient();
  
  if (!redis) {
    console.warn('Cannot ban email without Redis');
    return;
  }
  
  try {
    await redis.connect();
    const emailHash = hashEmail(email);
    await redis.set(`ban:email:${emailHash}`, JSON.stringify({ reason, banned_at: new Date().toISOString() }), 'EX', durationSeconds);
    console.log(`Banned email ${email} for ${durationSeconds}s: ${reason}`);
  } catch (error) {
    console.error('Failed to ban email:', error);
  }
}

/**
 * Get client IP address
 */
export function getClientIP(request: Request): string {
  // Check Cloudflare header
  const cfConnectingIP = request.headers.get('cf-connecting-ip');
  if (cfConnectingIP) return cfConnectingIP;
  
  // Check X-Forwarded-For
  const xForwardedFor = request.headers.get('x-forwarded-for');
  if (xForwardedFor) {
    const ips = xForwardedFor.split(',');
    return ips[0].trim();
  }
  
  // Check X-Real-IP
  const xRealIP = request.headers.get('x-real-ip');
  if (xRealIP) return xRealIP;
  
  return 'unknown';
}

/**
 * Hash email for privacy
 */
function hashEmail(email: string): string {
  // Simple hash - in production use crypto.subtle.digest
  let hash = 0;
  for (let i = 0; i < email.length; i++) {
    const char = email.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

/**
 * Combined rate limit check
 */
export async function checkAllRateLimits(ip: string, email?: string): Promise<{
  allowed: boolean;
  reason?: string;
  resetAt?: Date;
}> {
  // Check ban list first
  const isBanned = await checkBanList(ip, email);
  if (isBanned) {
    return { allowed: false, reason: 'Banned' };
  }
  
  // Check global rate limit
  const globalLimit = await checkGlobalRateLimit();
  if (!globalLimit.allowed) {
    return { allowed: false, reason: 'Global rate limit exceeded', resetAt: globalLimit.resetAt };
  }
  
  // Check IP rate limit
  const ipLimit = await checkIPRateLimit(ip);
  if (!ipLimit.allowed) {
    return { allowed: false, reason: 'IP rate limit exceeded (20/hour)', resetAt: ipLimit.resetAt };
  }
  
  // Check email rate limit (if provided)
  if (email) {
    const emailLimit = await checkEmailRateLimit(email);
    if (!emailLimit.allowed) {
      return { allowed: false, reason: 'Email rate limit exceeded (3/day)', resetAt: emailLimit.resetAt };
    }
  }
  
  return { allowed: true };
}

/**
 * Format rate limit error response
 */
export function formatRateLimitError(resetAt: Date): {
  error: string;
  code: string;
  retry_after: number;
} {
  const retryAfter = Math.ceil((resetAt.getTime() - Date.now()) / 1000);
  
  return {
    error: `Rate limit exceeded. Try again in ${retryAfter} seconds.`,
    code: 'RATE_LIMIT_EXCEEDED',
    retry_after: retryAfter
  };
}



