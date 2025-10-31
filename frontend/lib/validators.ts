/**
 * Free Tool Validators
 * 
 * Validates file uploads, email addresses, and request data
 * for the free statement categorizer tool.
 */

import { z } from 'zod';

// Default configuration (can be overridden by server-side config)
export const DEFAULT_FREE_TOOL_CONFIG = {
  max_rows: 500,
  max_file_mb: { csv: 10, pdf: 50, image: 25, zip: 200 },
  allowed_ext: ['csv', 'ofx', 'qfx', 'pdf', 'jpg', 'jpeg', 'png', 'zip'],
  allowed_mime: [
    'text/csv',
    'text/comma-separated-values',
    'application/vnd.ms-excel',
    'application/x-ofx',
    'application/vnd.intu.qfx',
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/zip',
    'application/x-zip-compressed'
  ],
  rate_limit: { ip_per_hour: 20, email_per_day: 3 },
  retention_hours: 24
};

export function getFreeToolConfig() {
  // In client-side code, just return defaults
  // Server-side code can override by loading from YAML
  return DEFAULT_FREE_TOOL_CONFIG;
}

// File extension to MIME type mapping
const EXT_TO_MIME: Record<string, string[]> = {
  csv: ['text/csv', 'text/comma-separated-values', 'application/vnd.ms-excel'],
  ofx: ['application/x-ofx', 'application/vnd.intu.qfx'],
  qfx: ['application/x-ofx', 'application/vnd.intu.qfx'],
  pdf: ['application/pdf'],
  jpg: ['image/jpeg'],
  jpeg: ['image/jpeg'],
  png: ['image/png'],
  zip: ['application/zip', 'application/x-zip-compressed']
};

// Magic bytes for file type detection
const MAGIC_BYTES: Record<string, number[]> = {
  pdf: [0x25, 0x50, 0x44, 0x46], // %PDF
  jpg: [0xFF, 0xD8, 0xFF],
  png: [0x89, 0x50, 0x4E, 0x47],
  zip: [0x50, 0x4B, 0x03, 0x04]
};

/**
 * Validate file extension against allowed list
 */
export function validateExtension(filename: string): { valid: boolean; extension?: string; error?: string } {
  const config = getFreeToolConfig();
  const ext = filename.split('.').pop()?.toLowerCase();
  
  if (!ext) {
    return { valid: false, error: 'File has no extension' };
  }
  
  if (!config.allowed_ext.includes(ext)) {
    return {
      valid: false,
      error: `File type '.${ext}' not supported. Allowed: ${config.allowed_ext.join(', ')}`
    };
  }
  
  return { valid: true, extension: ext };
}

/**
 * Validate file size against limits
 */
export function validateFileSize(sizeBytes: number, extension: string): { valid: boolean; error?: string } {
  const config = getFreeToolConfig();
  const sizeMB = sizeBytes / (1024 * 1024);
  
  let maxSizeMB: number;
  
  if (['csv', 'ofx', 'qfx'].includes(extension)) {
    maxSizeMB = config.max_file_mb.csv || 10;
  } else if (extension === 'pdf') {
    maxSizeMB = config.max_file_mb.pdf || 50;
  } else if (['jpg', 'jpeg', 'png'].includes(extension)) {
    maxSizeMB = config.max_file_mb.image || 25;
  } else if (extension === 'zip') {
    maxSizeMB = config.max_file_mb.zip || 200;
  } else {
    maxSizeMB = 10; // default
  }
  
  if (sizeMB > maxSizeMB) {
    return {
      valid: false,
      error: `File too large (${sizeMB.toFixed(1)} MB). Max for .${extension} is ${maxSizeMB} MB`
    };
  }
  
  return { valid: true };
}

/**
 * Validate MIME type
 */
export function validateMimeType(mimeType: string, extension: string): { valid: boolean; error?: string } {
  const allowedMimes = EXT_TO_MIME[extension];
  
  if (!allowedMimes) {
    return { valid: false, error: `Unknown file type: .${extension}` };
  }
  
  // Allow application/octet-stream as fallback (will check magic bytes)
  if (mimeType === 'application/octet-stream') {
    return { valid: true };
  }
  
  if (!allowedMimes.includes(mimeType)) {
    return {
      valid: false,
      error: `MIME type '${mimeType}' doesn't match extension '.${extension}'`
    };
  }
  
  return { valid: true };
}

/**
 * Check file magic bytes
 */
export async function validateMagicBytes(buffer: Buffer, extension: string): Promise<{ valid: boolean; error?: string }> {
  const magicBytes = MAGIC_BYTES[extension];
  
  if (!magicBytes) {
    // No magic bytes to check for this type
    return { valid: true };
  }
  
  const fileBytes = Array.from(buffer.slice(0, magicBytes.length));
  const matches = magicBytes.every((byte, i) => fileBytes[i] === byte);
  
  if (!matches) {
    return {
      valid: false,
      error: `File content doesn't match .${extension} format`
    };
  }
  
  return { valid: true };
}

/**
 * Check if PDF is password-protected
 */
export async function checkPasswordProtectedPDF(buffer: Buffer): Promise<boolean> {
  const content = buffer.toString('latin1');
  return content.includes('/Encrypt');
}

/**
 * Comprehensive file validation
 */
export async function validateFile(
  file: File | { name: string; size: number; type: string },
  buffer?: Buffer
): Promise<{ valid: boolean; errors: string[] }> {
  const errors: string[] = [];
  
  // Extension validation
  const extValidation = validateExtension(file.name);
  if (!extValidation.valid) {
    errors.push(extValidation.error!);
    return { valid: false, errors };
  }
  
  const extension = extValidation.extension!;
  
  // Size validation
  const sizeValidation = validateFileSize(file.size, extension);
  if (!sizeValidation.valid) {
    errors.push(sizeValidation.error!);
  }
  
  // MIME type validation
  const mimeValidation = validateMimeType(file.type, extension);
  if (!mimeValidation.valid) {
    errors.push(mimeValidation.error!);
  }
  
  // Magic bytes validation (if buffer provided)
  if (buffer) {
    const magicValidation = await validateMagicBytes(buffer, extension);
    if (!magicValidation.valid) {
      errors.push(magicValidation.error!);
    }
    
    // Check for password-protected PDF
    if (extension === 'pdf') {
      const isPasswordProtected = await checkPasswordProtectedPDF(buffer);
      if (isPasswordProtected) {
        errors.push('PDF is password-protected. Please remove password and try again.');
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

// Zod schemas for API validation

export const uploadSchema = z.object({
  captcha_token: z.string().min(1, 'CAPTCHA required'),
  utm_source: z.string().optional(),
  utm_medium: z.string().optional(),
  utm_campaign: z.string().optional()
});

export const proposeSchema = z.object({
  upload_id: z.string().uuid('Invalid upload ID')
});

export const verifyEmailSendSchema = z.object({
  email: z.string().email('Invalid email address'),
  captcha_token: z.string().min(1, 'CAPTCHA required')
});

export const verifyEmailConfirmSchema = z.object({
  email: z.string().email('Invalid email address'),
  code: z.string().length(6, 'Code must be 6 digits').regex(/^\d{6}$/, 'Code must be numeric')
});

export const exportCsvSchema = z.object({
  upload_id: z.string().uuid('Invalid upload ID'),
  email_token: z.string().min(1, 'Email verification required'),
  consent: z.boolean().refine(val => val === true, 'Consent required')
});

/**
 * Email validation
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Extract email domain
 */
export function getEmailDomain(email: string): string {
  return email.split('@')[1] || '';
}

/**
 * Sanitize filename
 */
export function sanitizeFilename(filename: string): string {
  return filename.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 255);
}

/**
 * Truncate description for privacy
 */
export function truncateDescription(desc: string, maxLength: number = 80): string {
  if (desc.length <= maxLength) return desc;
  return desc.slice(0, maxLength) + '...';
}

/**
 * Hash text for logging (privacy-safe)
 */
export function hashForLogging(text: string): string {
  // Simple hash for privacy - in production use crypto.subtle.digest
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

/**
 * Validate UTM parameters
 */
export function validateUTMParams(params: Record<string, any>): {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
} {
  return {
    utm_source: typeof params.utm_source === 'string' ? params.utm_source : undefined,
    utm_medium: typeof params.utm_medium === 'string' ? params.utm_medium : undefined,
    utm_campaign: typeof params.utm_campaign === 'string' ? params.utm_campaign : undefined
  };
}

/**
 * Validate row limit
 */
export function validateRowLimit(rowCount: number): { valid: boolean; capped: boolean; limit: number } {
  const config = getFreeToolConfig();
  const limit = config.max_rows || 500;
  
  if (rowCount <= limit) {
    return { valid: true, capped: false, limit };
  }
  
  return { valid: true, capped: true, limit };
}

