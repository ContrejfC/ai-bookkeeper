'use server';

/**
 * Free Categorizer Server Actions v2
 * ==================================
 * 
 * Updated for combined upload+parse flow and Next.js API routes.
 */

import { cookies } from 'next/headers';
import { sanitizeCsvTable, rowsToCsv } from '@/lib/csv_sanitize';

interface UploadResult {
  success: boolean;
  uploadId?: string;
  filename?: string;
  rowCount?: number;
  transactions?: any[];
  error?: string;
  code?: string;
}

interface VerifyEmailResult {
  success: boolean;
  message?: string;
  token?: string;
  error?: string;
  code?: string;
}

interface ExportResult {
  success: boolean;
  csvData?: string;
  filename?: string;
  error?: string;
  code?: string;
}

/**
 * Upload is now handled by Next.js API route at /api/free/categorizer/upload
 * This returns both upload confirmation AND parsed transactions
 */

/**
 * Send verification code via email
 */
export async function sendVerificationCode(email: string): Promise<VerifyEmailResult> {
  try {
    // Generate 6-digit code
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Store code in cookie (expires in 15 minutes)
    const cookieStore = await cookies();
    cookieStore.set('verification_code', code, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 15 * 60, // 15 minutes
      sameSite: 'lax'
    });
    
    cookieStore.set('verification_email', email, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 15 * 60,
      sameSite: 'lax'
    });
    
    cookieStore.set('verification_sent_at', Date.now().toString(), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 15 * 60,
      sameSite: 'lax'
    });
    
    // TODO: Send actual email via SendGrid/Resend
    // For now, log to console (development)
    console.log(`[DEV] Verification code for ${email}: ${code}`);
    
    return {
      success: true,
      message: 'Verification code sent'
    };
    
  } catch (error) {
    console.error('Send verification error:', error);
    return {
      success: false,
      error: 'Failed to send verification code',
      code: 'GENERIC_ERROR'
    };
  }
}

/**
 * Verify email code and issue token
 */
export async function verifyEmailCode(email: string, code: string): Promise<VerifyEmailResult> {
  try {
    const cookieStore = await cookies();
    const storedCode = cookieStore.get('verification_code')?.value;
    const storedEmail = cookieStore.get('verification_email')?.value;
    
    if (!storedCode || !storedEmail) {
      return {
        success: false,
        error: 'Verification code expired',
        code: 'CODE_EXPIRED'
      };
    }
    
    if (storedEmail !== email) {
      return {
        success: false,
        error: 'Email mismatch',
        code: 'EMAIL_INVALID'
      };
    }
    
    if (storedCode !== code) {
      return {
        success: false,
        error: 'Invalid code',
        code: 'TOKEN_INVALID'
      };
    }
    
    // Generate email token
    const token = Buffer.from(JSON.stringify({ email, verified: true, ts: Date.now() })).toString('base64');
    
    // Store token in cookie
    cookieStore.set('email_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60, // 1 hour
      sameSite: 'lax'
    });
    
    // Clear verification cookies
    cookieStore.delete('verification_code');
    cookieStore.delete('verification_email');
    cookieStore.delete('verification_sent_at');
    
    return {
      success: true,
      token
    };
    
  } catch (error) {
    console.error('Verify code error:', error);
    return {
      success: false,
      error: 'Verification failed',
      code: 'GENERIC_ERROR'
    };
  }
}

/**
 * Export categorized CSV
 */
export async function exportCategorizedCSV(uploadId: string): Promise<ExportResult> {
  try {
    const uploadDir = process.env.FREE_UPLOAD_DIR || '/tmp/free_uploads';
    const { readFile: readFileNode } = await import('fs/promises');
    const { join: joinPath } = await import('path');
    
    // Read metadata
    const metadataPath = joinPath(uploadDir, `${uploadId}_metadata.json`);
    const metadataContent = await readFileNode(metadataPath, 'utf-8');
    const metadata = JSON.parse(metadataContent);
    
    // Read original file
    const sanitizedFilename = metadata.filename.replace(/[^a-zA-Z0-9._-]/g, '_');
    const filePath = joinPath(uploadDir, `${uploadId}_${sanitizedFilename}`);
    const fileContent = await readFileNode(filePath, 'utf-8');
    
    // Parse CSV into rows for sanitization
    const lines = fileContent.split('\n').filter(line => line.trim());
    const limitedLines = lines.slice(0, FREE_MAX_ROWS + 1); // Header + 500 rows
    
    // Parse each line into fields (simple CSV parsing)
    const rows = limitedLines.map(line => {
      // Basic CSV parsing (handle quoted fields)
      const fields: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          fields.push(current);
          current = '';
        } else {
          current += char;
        }
      }
      fields.push(current); // Last field
      
      return fields;
    });
    
    // Sanitize CSV to prevent formula injection
    const sanitizedRows = sanitizeCsvTable(rows);
    
    // Convert back to CSV with watermark
    const watermarkLines = [
      '# Generated by AI Bookkeeper Free Tool • Watermarked • Not for production use',
      ''
    ];
    const csvRows = rowsToCsv(sanitizedRows);
    
    let csvData = watermarkLines.join('\n') + '\n' + csvRows;
    
    if (lines.length > FREE_MAX_ROWS + 1) {
      csvData += '\n\n# *** Truncated at ' + FREE_MAX_ROWS + ' rows. Upgrade to process unlimited rows ***';
    }
    
    const filename = `free_${new Date().toISOString().split('T')[0]}_categorized.csv`;
    
    return {
      success: true,
      csvData,
      filename
    };
    
  } catch (error) {
    console.error('Export error:', error);
    return {
      success: false,
      error: 'Export failed',
      code: 'GENERIC_ERROR'
    };
  }
}

/**
 * Delete upload
 */
export async function deleteUpload(uploadId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(`/api/free/categorizer/uploads/${uploadId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error('Delete failed');
    }
    
    return { success: true };
  } catch (error) {
    console.error('Delete error:', error);
    return {
      success: false,
      error: 'Failed to delete upload'
    };
  }
}

/**
 * Save feedback (stub - not used in v1)
 */
export async function saveFeedback(
  uploadId: string,
  feedback: Record<string, string>,
  previewRows: any[]
): Promise<{ success: boolean; error?: string }> {
  // Feedback saving is optional for v1
  return { success: true };
}

const FREE_MAX_ROWS = parseInt(process.env.FREE_MAX_ROWS || '500', 10);

