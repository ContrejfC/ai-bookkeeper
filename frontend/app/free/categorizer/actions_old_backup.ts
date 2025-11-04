'use server';

/**
 * Free Categorizer Server Actions
 * 
 * Server-side actions for the free statement categorizer tool.
 * Handles backend API calls with proper error handling and telemetry.
 */

import { cookies } from 'next/headers';

interface UploadResult {
  success: boolean;
  uploadId?: string;
  filename?: string;
  error?: string;
  code?: string;
}

interface ProposeResult {
  success: boolean;
  previewRows?: any[];
  totalRows?: number;
  categoriesCount?: number;
  confidenceAvg?: number;
  metrics?: any;
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
 * Get backend API base URL
 */
function getBackendApiBase(): string {
  return process.env.BACKEND_API_BASE || 'http://localhost:8000';
}

/**
 * Get backend API key
 */
function getBackendApiKey(): string | undefined {
  return process.env.BACKEND_API_KEY;
}

/**
 * Call backend ingestion API to propose categories
 */
export async function proposeCategorization(uploadId: string): Promise<ProposeResult> {
  try {
    const apiBase = getBackendApiBase();
    const apiKey = getBackendApiKey();
    
    // Call backend propose endpoint
    const response = await fetch(`${apiBase}/api/propose`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Free-Mode': 'true',
        'X-Rate-Limited': 'true',
        ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
      },
      body: JSON.stringify({
        upload_id: uploadId,
        max_rows: 500, // Free tier limit
        preview_rows: 25 // Preview limit
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      return {
        success: false,
        error: error.message || 'Categorization failed',
        code: error.code || 'PROPOSE_FAILED'
      };
    }
    
    const result = await response.json();
    
    // Truncate descriptions for privacy
    const previewRows = result.preview_rows?.map((row: any) => ({
      ...row,
      description: row.description?.slice(0, 80) || ''
    }));
    
    return {
      success: true,
      previewRows: previewRows || [],
      totalRows: result.total_rows || 0,
      categoriesCount: result.categories_count || 0,
      confidenceAvg: result.confidence_avg || 0,
      metrics: result.metrics
    };
    
  } catch (error) {
    console.error('Propose error:', error);
    return {
      success: false,
      error: 'Failed to categorize transactions',
      code: 'PROPOSE_ERROR'
    };
  }
}

/**
 * Send email verification code
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
    
    // Send email via provider
    await sendEmailCode(email, code);
    
    return {
      success: true,
      message: 'Verification code sent to your email'
    };
    
  } catch (error) {
    console.error('Send verification error:', error);
    return {
      success: false,
      error: 'Failed to send verification code',
      code: 'EMAIL_SEND_FAILED'
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
    
    if (storedEmail !== email || storedCode !== code) {
      return {
        success: false,
        error: 'Invalid verification code',
        code: 'CODE_INVALID'
      };
    }
    
    // Generate JWT token (simplified - use proper JWT library in production)
    const token = Buffer.from(JSON.stringify({
      email,
      verified_at: Date.now(),
      expires_at: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
    })).toString('base64');
    
    // Store token in cookie
    cookieStore.set('email_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 24 * 60 * 60, // 24 hours
      sameSite: 'lax'
    });
    
    // Clear verification cookies
    cookieStore.delete('verification_code');
    cookieStore.delete('verification_email');
    
    return {
      success: true,
      message: 'Email verified successfully',
      token
    };
    
  } catch (error) {
    console.error('Verify code error:', error);
    return {
      success: false,
      error: 'Verification failed',
      code: 'VERIFY_FAILED'
    };
  }
}

/**
 * Export categorized CSV with watermark
 */
export async function exportCategorizedCSV(uploadId: string): Promise<ExportResult> {
  try {
    const cookieStore = await cookies();
    const emailToken = cookieStore.get('email_token')?.value;
    
    if (!emailToken) {
      return {
        success: false,
        error: 'Email verification required',
        code: 'EMAIL_NOT_VERIFIED'
      };
    }
    
    // Verify token
    const tokenData = JSON.parse(Buffer.from(emailToken, 'base64').toString());
    if (tokenData.expires_at < Date.now()) {
      return {
        success: false,
        error: 'Email verification expired',
        code: 'TOKEN_EXPIRED'
      };
    }
    
    const apiBase = getBackendApiBase();
    const apiKey = getBackendApiKey();
    
    // Get categorized data from backend
    const response = await fetch(`${apiBase}/api/export/csv`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Free-Mode': 'true',
        ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
      },
      body: JSON.stringify({
        upload_id: uploadId,
        max_rows: 500,
        format: 'csv'
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      return {
        success: false,
        error: error.message || 'Export failed',
        code: error.code || 'EXPORT_FAILED'
      };
    }
    
    const data = await response.json();
    
    // Apply watermark
    const watermarkedCSV = applyWatermark(data.rows || []);
    
    const filename = `free_${new Date().toISOString().split('T')[0]}_categorized.csv`;
    
    return {
      success: true,
      csvData: watermarkedCSV,
      filename
    };
    
  } catch (error) {
    console.error('Export error:', error);
    return {
      success: false,
      error: 'Failed to export CSV',
      code: 'EXPORT_ERROR'
    };
  }
}

/**
 * Apply watermark to CSV data
 */
function applyWatermark(rows: any[]): string {
  const lines: string[] = [];
  
  // Add watermark header comment
  lines.push('# Generated by AI-Bookkeeper Free Tool • Watermarked • Not for production use');
  lines.push('');
  
  // Add CSV header with watermark column
  lines.push('date,description,amount,category,confidence,notes,free_tier');
  
  // Add rows (capped at 500)
  const cappedRows = rows.slice(0, 500);
  
  for (const row of cappedRows) {
    const csvRow = [
      row.date || '',
      escapeCSV(row.description || ''),
      row.amount?.toFixed(2) || '0.00',
      escapeCSV(row.category || ''),
      row.confidence?.toFixed(2) || '0.00',
      escapeCSV(row.notes || ''),
      'watermarked'
    ].join(',');
    
    lines.push(csvRow);
  }
  
  // Add footer note if truncated
  if (rows.length > 500) {
    lines.push('');
    lines.push('# *** Truncated at 500 rows. Upgrade to process unlimited rows ***');
  }
  
  return lines.join('\n');
}

/**
 * Escape CSV field
 */
function escapeCSV(field: string): string {
  if (!field) return '';
  
  // Escape quotes and wrap in quotes if contains comma, quote, or newline
  if (field.includes(',') || field.includes('"') || field.includes('\n')) {
    return `"${field.replace(/"/g, '""')}"`;
  }
  
  return field;
}

/**
 * Send email code via provider
 */
async function sendEmailCode(email: string, code: string): Promise<void> {
  const provider = process.env.EMAIL_PROVIDER || 'sendgrid';
  const apiKey = process.env.EMAIL_PROVIDER_API_KEY;
  const from = process.env.EMAIL_FROM || 'no-reply@aibookkeeper.com';
  
  if (!apiKey) {
    console.warn('EMAIL_PROVIDER_API_KEY not set, skipping email send');
    return;
  }
  
  if (provider === 'sendgrid') {
    await sendViaSendGrid(email, code, apiKey, from);
  } else if (provider === 'mailgun') {
    await sendViaMailgun(email, code, apiKey, from);
  } else {
    console.log(`[DEV] Verification code for ${email}: ${code}`);
  }
}

/**
 * Send via SendGrid
 */
async function sendViaSendGrid(to: string, code: string, apiKey: string, from: string): Promise<void> {
  await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      personalizations: [{
        to: [{ email: to }]
      }],
      from: { email: from },
      subject: 'Your AI-Bookkeeper Verification Code',
      content: [{
        type: 'text/html',
        value: `
          <h2>Your Verification Code</h2>
          <p>Enter this code to download your categorized CSV:</p>
          <h1 style="font-size: 32px; letter-spacing: 8px; font-family: monospace;">${code}</h1>
          <p>This code expires in 15 minutes.</p>
          <p>If you didn't request this, please ignore this email.</p>
        `
      }]
    })
  });
}

/**
 * Send via Mailgun
 */
async function sendViaMailgun(to: string, code: string, apiKey: string, from: string): Promise<void> {
  const domain = process.env.MAILGUN_DOMAIN || 'mg.aibookkeeper.com';
  
  const formData = new FormData();
  formData.append('from', from);
  formData.append('to', to);
  formData.append('subject', 'Your AI-Bookkeeper Verification Code');
  formData.append('html', `
    <h2>Your Verification Code</h2>
    <p>Enter this code to download your categorized CSV:</p>
    <h1 style="font-size: 32px; letter-spacing: 8px; font-family: monospace;">${code}</h1>
    <p>This code expires in 15 minutes.</p>
    <p>If you didn't request this, please ignore this email.</p>
  `);
  
  await fetch(`https://api.mailgun.net/v3/${domain}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${Buffer.from(`api:${apiKey}`).toString('base64')}`
    },
    body: formData
  });
}

/**
 * Save user feedback for training the AI model
 */
export async function saveFeedback(
  uploadId: string,
  feedback: Record<string, string>,
  transactions: Array<{
    id: string;
    date: string;
    description: string;
    amount: number;
    category: string;
    confidence: number;
  }>
): Promise<{ success: boolean; error?: string }> {
  try {
    // Build training data format
    const trainingData = Object.entries(feedback).map(([txnId, userCategory]) => {
      const txn = transactions.find(t => (t.id || `txn_${transactions.indexOf(t)}`) === txnId);
      if (!txn) return null;
      
      return {
        id: txnId,
        date: txn.date,
        description: txn.description.substring(0, 100), // Truncate for privacy
        amount: txn.amount,
        original_category: txn.category,
        original_confidence: txn.confidence,
        user_category: userCategory
      };
    }).filter(Boolean);

    // Call feedback API
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/api/free/save_feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        upload_id: uploadId,
        feedback,
        transactions: trainingData
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('[FEEDBACK] Save failed:', error);
      return {
        success: false,
        error: error.hint || 'Failed to save feedback'
      };
    }

    const result = await response.json();
    console.log(`[FEEDBACK] Saved ${trainingData.length} feedback entries`);
    
    return {
      success: true
    };

  } catch (error) {
    console.error('[FEEDBACK] Error saving feedback:', error);
    return {
      success: false,
      error: 'Failed to save feedback'
    };
  }
}

/**
 * Delete upload and all associated data
 */
export async function deleteUpload(uploadId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const apiBase = getBackendApiBase();
    const apiKey = getBackendApiKey();
    
    const response = await fetch(`${apiBase}/api/free/categorizer/uploads/${uploadId}`, {
      method: 'DELETE',
      headers: {
        'X-Free-Mode': 'true',
        ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
      }
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

