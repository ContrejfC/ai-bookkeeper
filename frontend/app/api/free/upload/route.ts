/**
 * Free Tool Upload API Route
 * 
 * Handles file uploads for the free categorizer tool.
 * Validates files, checks rate limits, stores to temp directory.
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { v4 as uuidv4 } from 'uuid';
import { validateFile } from '@/lib/validators';
import { checkAllRateLimits, getClientIP } from '@/lib/rateLimit';

export async function POST(request: NextRequest) {
  try {
    // Get client IP
    const ip = getClientIP(request);
    
    // Check rate limits
    const rateLimitResult = await checkAllRateLimits(ip);
    
    if (!rateLimitResult.allowed) {
      return NextResponse.json(
        {
          error: rateLimitResult.reason,
          code: 'RATE_LIMIT_EXCEEDED',
          retry_after: rateLimitResult.resetAt ? Math.ceil((rateLimitResult.resetAt.getTime() - Date.now()) / 1000) : 3600
        },
        { status: 429 }
      );
    }
    
    // Parse multipart form data
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const captchaToken = formData.get('captcha_token') as string;
    
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided', code: 'FILE_MISSING' },
        { status: 400 }
      );
    }
    
    if (!captchaToken) {
      return NextResponse.json(
        { error: 'CAPTCHA required', code: 'CAPTCHA_MISSING' },
        { status: 400 }
      );
    }
    
    // Verify CAPTCHA
    const captchaValid = await verifyCaptcha(captchaToken, ip);
    
    if (!captchaValid) {
      return NextResponse.json(
        { error: 'CAPTCHA verification failed', code: 'CAPTCHA_INVALID' },
        { status: 400 }
      );
    }
    
    // Read file buffer
    const buffer = Buffer.from(await file.arrayBuffer());
    
    // Validate file
    const validation = await validateFile(file, buffer);
    
    if (!validation.valid) {
      return NextResponse.json(
        {
          error: validation.errors[0],
          code: 'FILE_INVALID',
          errors: validation.errors
        },
        { status: 400 }
      );
    }
    
    // Generate upload ID
    const uploadId = uuidv4();
    
    // Store file to temp directory
    const tempDir = process.env.TEMP_STORAGE_PATH || '/tmp/free_uploads';
    const uploadDir = join(tempDir, uploadId);
    
    await mkdir(uploadDir, { recursive: true });
    
    const filePath = join(uploadDir, file.name);
    await writeFile(filePath, buffer);
    
    // Store metadata
    const metadata = {
      upload_id: uploadId,
      filename: file.name,
      size_bytes: file.size,
      mime_type: file.type,
      uploaded_at: new Date().toISOString(),
      uploaded_by_ip: ip,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
      utm_source: formData.get('utm_source') || undefined,
      utm_medium: formData.get('utm_medium') || undefined,
      utm_campaign: formData.get('utm_campaign') || undefined
    };
    
    const metadataPath = join(uploadDir, 'metadata.json');
    await writeFile(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Schedule deletion after 24 hours (would use a job queue in production)
    scheduleFileDeletion(uploadDir, 24 * 60 * 60 * 1000);
    
    return NextResponse.json({
      upload_id: uploadId,
      filename: file.name,
      size_bytes: file.size,
      mime_type: file.type
    });
    
  } catch (error) {
    console.error('Upload error:', error);
    
    return NextResponse.json(
      {
        error: 'Upload failed',
        code: 'UPLOAD_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

/**
 * Verify CAPTCHA token
 */
async function verifyCaptcha(token: string, ip: string): Promise<boolean> {
  const provider = process.env.CAPTCHA_PROVIDER || 'turnstile';
  
  if (provider === 'turnstile') {
    return verifyTurnstile(token, ip);
  } else if (provider === 'hcaptcha') {
    return verifyHCaptcha(token, ip);
  }
  
  // In development, allow without verification
  if (process.env.NODE_ENV !== 'production') {
    return true;
  }
  
  return false;
}

/**
 * Verify Cloudflare Turnstile
 */
async function verifyTurnstile(token: string, ip: string): Promise<boolean> {
  const secret = process.env.TURNSTILE_SECRET_KEY;
  
  if (!secret) {
    console.warn('TURNSTILE_SECRET_KEY not set');
    return true; // Fail open in development
  }
  
  try {
    const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        secret,
        response: token,
        remoteip: ip
      })
    });
    
    const data = await response.json();
    return data.success === true;
    
  } catch (error) {
    console.error('Turnstile verification error:', error);
    return false;
  }
}

/**
 * Verify hCaptcha
 */
async function verifyHCaptcha(token: string, ip: string): Promise<boolean> {
  const secret = process.env.HCAPTCHA_SECRET_KEY;
  
  if (!secret) {
    console.warn('HCAPTCHA_SECRET_KEY not set');
    return true;
  }
  
  try {
    const params = new URLSearchParams({
      secret,
      response: token,
      remoteip: ip
    });
    
    const response = await fetch('https://hcaptcha.com/siteverify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    });
    
    const data = await response.json();
    return data.success === true;
    
  } catch (error) {
    console.error('hCaptcha verification error:', error);
    return false;
  }
}

/**
 * Schedule file deletion (simplified - use job queue in production)
 */
function scheduleFileDeletion(dir: string, delayMs: number): void {
  // In production, this would push to a job queue like Bull or BullMQ
  // For now, use setTimeout (not reliable across restarts)
  setTimeout(async () => {
    try {
      const { rm } = await import('fs/promises');
      await rm(dir, { recursive: true, force: true });
      console.log(`Deleted temp directory: ${dir}`);
    } catch (error) {
      console.error(`Failed to delete temp directory ${dir}:`, error);
    }
  }, delayMs);
}



