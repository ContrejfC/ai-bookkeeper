/**
 * Free Categorizer Lead Capture
 * =============================
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir, readFile } from 'fs/promises';
import { join } from 'path';
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, uploadId, rows } = body;
    
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Invalid email', code: 'EMAIL_INVALID' },
        { status: 400 }
      );
    }
    
    if (!uploadId) {
      return NextResponse.json(
        { error: 'Upload ID required', code: 'GENERIC_ERROR' },
        { status: 400 }
      );
    }
    
    // Hash IP
    const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown';
    const ipSalt = process.env.IP_HASH_SALT || 'default-salt-change-in-prod';
    const ipHash = crypto.createHash('sha256').update(ip + ipSalt).digest('hex');
    
    // Create lead record
    const leadId = uuidv4();
    const lead = {
      id: leadId,
      created_at: new Date().toISOString(),
      email,
      upload_id: uploadId,
      row_count: rows || 0,
      source: 'free_categorizer',
      ip_hash: ipHash,
      contacted: false,
      converted: false
    };
    
    // Save to leads directory
    const leadsDir = join(process.env.FREE_UPLOAD_DIR || '/tmp/free_uploads', 'leads');
    await mkdir(leadsDir, { recursive: true });
    
    const leadPath = join(leadsDir, `${leadId}.json`);
    await writeFile(leadPath, JSON.stringify(lead, null, 2));
    
    return NextResponse.json({
      success: true,
      message: 'Lead captured',
      leadId
    });
    
  } catch (error) {
    console.error('Lead capture error:', error);
    return NextResponse.json(
      { error: 'Failed to capture lead', code: 'GENERIC_ERROR' },
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

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

