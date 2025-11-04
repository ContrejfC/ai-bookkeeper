/**
 * Delete Free Tool Upload
 * =======================
 */

import { NextRequest, NextResponse } from 'next/server';
import { unlink } from 'fs/promises';
import { join } from 'path';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const uploadId = params.id;
    const uploadDir = process.env.FREE_UPLOAD_DIR || '/tmp/free_uploads';
    
    // Read metadata to get filename
    const metadataPath = join(uploadDir, `${uploadId}_metadata.json`);
    
    let filename = 'unknown';
    try {
      const { readFile } = await import('fs/promises');
      const metadataContent = await readFile(metadataPath, 'utf-8');
      const metadata = JSON.parse(metadataContent);
      filename = metadata.filename;
    } catch (error) {
      // Metadata not found, but continue to try deleting the file
    }
    
    // Delete files
    const filePath = join(uploadDir, `${uploadId}_${filename.replace(/[^a-zA-Z0-9._-]/g, '_')}`);
    const consentLogPath = join(uploadDir, `consent_${uploadId}.json`);
    
    const deletePromises = [
      unlink(filePath).catch(() => {}),
      unlink(metadataPath).catch(() => {}),
      unlink(consentLogPath).catch(() => {})
    ];
    
    await Promise.all(deletePromises);
    
    return NextResponse.json({
      success: true,
      message: 'Upload deleted'
    });
    
  } catch (error) {
    console.error('Delete error:', error);
    return NextResponse.json(
      {
        error: 'Delete failed',
        code: 'GENERIC_ERROR'
      },
      { status: 500 }
    );
  }
}

// Method guards
export async function GET() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'DELETE' }
  });
}

export async function POST() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'DELETE' }
  });
}

export async function PUT() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'DELETE' }
  });
}

export async function PATCH() {
  return new Response('Method Not Allowed', {
    status: 405,
    headers: { 'Allow': 'DELETE' }
  });
}

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

