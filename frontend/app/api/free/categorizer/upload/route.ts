/**
 * Free Categorizer Upload Route
 * =============================
 * 
 * Handles file upload with:
 * - Node-compatible MIME validation (file-type)
 * - Encrypted PDF detection (pdf-lib)
 * - ZIP content validation (jszip)
 * - Combined upload + parse flow
 * - Consent tracking
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { v4 as uuidv4 } from 'uuid';
import { validateMimeType, isPDFEncrypted } from '@/lib/mime-validator';
import crypto from 'crypto';

const FREE_MAX_FILE_MB = parseInt(process.env.FREE_MAX_FILE_MB || '10', 10);
const FREE_MAX_ROWS = parseInt(process.env.FREE_MAX_ROWS || '500', 10);
const FREE_RETENTION_HOURS = parseInt(process.env.FREE_RETENTION_HOURS || '24', 10);

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const consentTraining = formData.get('consentTraining') === 'true';
    const utmSource = formData.get('utm_source') as string | null;
    const utmMedium = formData.get('utm_medium') as string | null;
    const utmCampaign = formData.get('utm_campaign') as string | null;
    
    if (!file) {
      return NextResponse.json(
        { 
          error: 'No file provided',
          code: 'GENERIC_ERROR'
        },
        { status: 400 }
      );
    }
    
    // Convert file to buffer
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    
    // Size validation
    const sizeMB = buffer.length / (1024 * 1024);
    
    if (sizeMB > FREE_MAX_FILE_MB) {
      return NextResponse.json(
        {
          error: `File exceeds ${FREE_MAX_FILE_MB} MB limit`,
          code: 'FILE_TOO_LARGE',
          context: {
            fileSizeMB: parseFloat(sizeMB.toFixed(1)),
            maxFileMB: FREE_MAX_FILE_MB
          }
        },
        { status: 400 }
      );
    }
    
    // MIME validation using magic bytes
    const mimeValidation = await validateMimeType(buffer, file.name);
    
    if (!mimeValidation.valid) {
      return NextResponse.json(
        {
          error: mimeValidation.error,
          code: mimeValidation.code || 'UNSUPPORTED_TYPE'
        },
        { status: 400 }
      );
    }
    
    // Check for encrypted PDF
    if (mimeValidation.mime === 'application/pdf') {
      const isEncrypted = await isPDFEncrypted(buffer);
      
      if (isEncrypted) {
        return NextResponse.json(
          {
            error: 'Password-protected PDFs are not supported',
            code: 'ENCRYPTED_PDF'
          },
          { status: 400 }
        );
      }
    }
    
    // Generate upload ID
    const uploadId = uuidv4();
    
    // Calculate expiration
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + FREE_RETENTION_HOURS);
    
    // Hash IP for privacy
    const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown';
    const ipSalt = process.env.IP_HASH_SALT || 'default-salt-change-in-prod';
    const ipHash = crypto.createHash('sha256').update(ip + ipSalt).digest('hex');
    
    // Hash file
    const fileHash = crypto.createHash('sha256').update(buffer).digest('hex');
    
    // Save file to temporary storage
    const uploadDir = process.env.FREE_UPLOAD_DIR || '/tmp/free_uploads';
    await mkdir(uploadDir, { recursive: true });
    
    const sanitizedFilename = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
    const filePath = join(uploadDir, `${uploadId}_${sanitizedFilename}`);
    await writeFile(filePath, buffer);
    
    // Save metadata to JSON file (simple storage for demo)
    const metadata = {
      id: uploadId,
      filename: file.name,
      size_bytes: buffer.length,
      mime_type: mimeValidation.mime,
      source_ext: mimeValidation.ext,
      created_at: new Date().toISOString(),
      expires_at: expiresAt.toISOString(),
      consent_training: consentTraining,
      consent_ts: consentTraining ? new Date().toISOString() : null,
      ip_hash: ipHash,
      file_hash: fileHash,
      retention_scope: 'ephemeral' as const,
      utm_source: utmSource,
      utm_medium: utmMedium,
      utm_campaign: utmCampaign,
      row_count: 0 as number
    };
    
    const metadataPath = join(uploadDir, `${uploadId}_metadata.json`);
    await writeFile(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Parse the file immediately (combined upload + parse)
    let rowCount = 0;
    let transactions: any[] = [];
    
    try {
      if (mimeValidation.ext === 'csv') {
        // Simple CSV parsing
        const text = buffer.toString('utf-8');
        const lines = text.split('\n').filter(l => l.trim());
        
        rowCount = Math.max(0, lines.length - 1); // Exclude header
        
        if (rowCount > FREE_MAX_ROWS) {
          // Delete the uploaded file
          await Promise.all([
            import('fs').then(fs => fs.promises.unlink(filePath)),
            import('fs').then(fs => fs.promises.unlink(metadataPath))
          ]);
          
          return NextResponse.json(
            {
              error: `File has ${rowCount} rows. Free limit is ${FREE_MAX_ROWS}.`,
              code: 'ROW_LIMIT_EXCEEDED',
              context: {
                rows: rowCount,
                maxRows: FREE_MAX_ROWS
              }
            },
            { status: 400 }
          );
        }
        
        // Parse rows (simple implementation)
        const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
        const dateIdx = headers.findIndex(h => h.includes('date'));
        const descIdx = headers.findIndex(h => h.includes('desc') || h.includes('memo') || h.includes('payee'));
        const amountIdx = headers.findIndex(h => h.includes('amount'));
        
        for (let i = 1; i < Math.min(lines.length, FREE_MAX_ROWS + 1); i++) {
          const values = lines[i].split(',');
          
          transactions.push({
            id: `${uploadId}_${i}`,
            date: values[dateIdx] || '',
            description: values[descIdx] || '',
            amount: parseFloat(values[amountIdx] || '0'),
            category: 'Uncategorized', // To be categorized by AI
            confidence: 0
          });
        }
      }
    } catch (error) {
      console.error('Parse error:', error);
      // Continue - parsing errors will be handled separately
    }
    
    // Update metadata with row count
    metadata.row_count = rowCount;
    await writeFile(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Log consent if granted
    if (consentTraining) {
      const consentLog = {
        id: uuidv4(),
        timestamp: new Date().toISOString(),
        upload_id: uploadId,
        consent_granted: true,
        file_hash_prefix: fileHash.substring(0, 16),
        metadata: {
          filename_hash: crypto.createHash('sha256').update(file.name).digest('hex').substring(0, 16)
        }
      };
      
      const consentLogPath = join(uploadDir, `consent_${uploadId}.json`);
      await writeFile(consentLogPath, JSON.stringify(consentLog, null, 2));
    }
    
    // Return response with parsed data
    return NextResponse.json({
      uploadId,
      upload_id: uploadId, // For backward compatibility
      filename: file.name,
      size_bytes: buffer.length,
      mime_type: mimeValidation.mime,
      row_count: rowCount,
      transactions: transactions.slice(0, 25), // Preview first 25
      total_rows: rowCount,
      expires_at: expiresAt.toISOString()
    });
    
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      {
        error: 'Upload failed',
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

