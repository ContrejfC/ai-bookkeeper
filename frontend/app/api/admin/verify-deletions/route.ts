/**
 * Deletion SLA Verifier
 * =====================
 * 
 * Admin endpoint to verify free tool data is being deleted within SLA (24 hours).
 * Protected by bearer token authentication.
 * 
 * Returns statistics about ephemeral uploads:
 * - p50Minutes: Median age of files
 * - p95Minutes: 95th percentile age
 * - staleCount: Files older than retention period
 * - total: Total files in ephemeral storage
 */

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from 'next/server';
import { readdir, stat } from 'fs/promises';
import { join } from 'path';

const FREE_RETENTION_HOURS = parseInt(process.env.FREE_RETENTION_HOURS || '24', 10);
const RETENTION_MS = FREE_RETENTION_HOURS * 60 * 60 * 1000;

export async function POST(request: NextRequest) {
  try {
    // Check authorization
    const authHeader = request.headers.get('authorization');
    const expectedToken = process.env.ADMIN_VERIFY_TOKEN;
    
    if (!expectedToken || expectedToken === 'change-me-long-random') {
      return NextResponse.json(
        { error: 'ADMIN_VERIFY_TOKEN not configured' },
        { status: 500 }
      );
    }
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Missing or invalid authorization header' },
        { status: 401 }
      );
    }
    
    const token = authHeader.slice(7); // Remove 'Bearer '
    
    if (token !== expectedToken) {
      return NextResponse.json(
        { error: 'Invalid token' },
        { status: 403 }
      );
    }
    
    // Scan ephemeral upload directory
    const uploadDir = process.env.FREE_UPLOAD_DIR || '/tmp/free_uploads';
    
    try {
      const files = await readdir(uploadDir);
      
      if (files.length === 0) {
        return NextResponse.json({
          p50Minutes: 0,
          p95Minutes: 0,
          staleCount: 0,
          total: 0,
          timestamp: new Date().toISOString()
        });
      }
      
      // Get ages of all files
      const now = Date.now();
      const fileAges: number[] = [];
      let staleCount = 0;
      
      for (const file of files) {
        try {
          const filePath = join(uploadDir, file);
          const stats = await stat(filePath);
          const ageMs = now - stats.mtimeMs;
          const ageMinutes = ageMs / (60 * 1000);
          
          fileAges.push(ageMinutes);
          
          if (ageMs > RETENTION_MS) {
            staleCount++;
          }
        } catch (err) {
          // Skip files that can't be stat'd
          continue;
        }
      }
      
      // Sort for percentile calculation
      fileAges.sort((a, b) => a - b);
      
      const p50Index = Math.floor(fileAges.length * 0.5);
      const p95Index = Math.floor(fileAges.length * 0.95);
      
      const p50Minutes = Math.round(fileAges[p50Index] || 0);
      const p95Minutes = Math.round(fileAges[p95Index] || 0);
      
      return NextResponse.json({
        p50Minutes,
        p95Minutes,
        staleCount,
        total: fileAges.length,
        retentionHours: FREE_RETENTION_HOURS,
        retentionMinutes: FREE_RETENTION_HOURS * 60,
        timestamp: new Date().toISOString()
      });
      
    } catch (dirError: any) {
      // Directory doesn't exist or can't be read
      if (dirError.code === 'ENOENT') {
        return NextResponse.json({
          p50Minutes: 0,
          p95Minutes: 0,
          staleCount: 0,
          total: 0,
          note: 'Upload directory does not exist yet',
          timestamp: new Date().toISOString()
        });
      }
      
      throw dirError;
    }
    
  } catch (error: any) {
    console.error('[verify-deletions] Error:', error);
    
    return NextResponse.json(
      { 
        error: String(error?.message || error),
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}

// Method guards
export async function GET() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'POST' }
  });
}

export async function PUT() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'POST' }
  });
}

export async function PATCH() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'POST' }
  });
}

export async function DELETE() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'POST' }
  });
}

