/**
 * Cron endpoint for purging expired free tool uploads
 * ===================================================
 * 
 * This route is called hourly by Vercel Cron to clean up
 * expired ephemeral uploads (> 24 hours old).
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get token from header
    const token = request.headers.get('x-purge-token') || request.headers.get('authorization')?.replace('Bearer ', '');
    
    // Validate token
    const adminToken = process.env.ADMIN_PURGE_TOKEN;
    
    if (!adminToken || token !== adminToken) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Call backend purge endpoint
    const backendBase = process.env.BACKEND_API_BASE || 'http://localhost:8000';
    const backendKey = process.env.BACKEND_API_KEY;
    
    const response = await fetch(`${backendBase}/api/free/categorizer/admin/purge-ephemeral`, {
      method: 'POST',
      headers: {
        'X-Purge-Token': adminToken,
        ...(backendKey && { 'Authorization': `Bearer ${backendKey}` })
      }
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: 'Purge failed', details: error },
        { status: 500 }
      );
    }
    
    const result = await response.json();
    
    return NextResponse.json(result);
    
  } catch (error) {
    console.error('Purge error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
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

// Allow Vercel Cron to call this
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

