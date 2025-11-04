/**
 * MIME Type Validation for Next.js/Node Runtime
 * =============================================
 * 
 * Uses file-type for magic byte detection (Node-compatible).
 */

import { fileTypeFromBuffer } from 'file-type';

const ALLOWED_MIME_TYPES = [
  'text/csv',
  'application/x-ofx',
  'application/vnd.intu.qfx',
  'application/pdf',
  'image/jpeg',
  'image/png',
  'application/zip',
  'application/x-zip-compressed'
];

const ALLOWED_EXTENSIONS = ['csv', 'ofx', 'qfx', 'pdf', 'jpg', 'jpeg', 'png', 'zip'];

export interface MimeValidationResult {
  valid: boolean;
  mime?: string;
  ext?: string;
  error?: string;
  code?: string;
}

/**
 * Validate file using magic bytes (server-side only)
 */
export async function validateMimeType(buffer: Buffer, filename: string): Promise<MimeValidationResult> {
  try {
    // Detect mime type from magic bytes
    const fileType = await fileTypeFromBuffer(buffer);
    
    // For text files like CSV, file-type returns undefined
    // Check if it looks like CSV by examining first few bytes
    if (!fileType) {
      const text = buffer.slice(0, 1024).toString('utf-8');
      
      // Check for CSV patterns
      if (text.includes(',') && (text.includes('\n') || text.includes('\r'))) {
        return {
          valid: true,
          mime: 'text/csv',
          ext: 'csv'
        };
      }
      
      // Check for OFX/QFX (XML-based)
      if (text.includes('<OFX>') || text.includes('OFXHEADER')) {
        return {
          valid: true,
          mime: 'application/x-ofx',
          ext: 'ofx'
        };
      }
      
      return {
        valid: false,
        error: 'Could not detect file type',
        code: 'UNSUPPORTED_TYPE'
      };
    }
    
    // Check if detected type is allowed
    if (!ALLOWED_MIME_TYPES.includes(fileType.mime)) {
      return {
        valid: false,
        mime: fileType.mime,
        ext: fileType.ext,
        error: `Unsupported file type: ${fileType.mime}`,
        code: 'UNSUPPORTED_TYPE'
      };
    }
    
    // If it's a ZIP, we need to validate contents
    if (fileType.mime === 'application/zip' || fileType.ext === 'zip') {
      const zipValidation = await validateZipContents(buffer);
      if (!zipValidation.valid) {
        return zipValidation;
      }
    }
    
    return {
      valid: true,
      mime: fileType.mime,
      ext: fileType.ext
    };
    
  } catch (error) {
    console.error('MIME validation error:', error);
    return {
      valid: false,
      error: 'File validation failed',
      code: 'GENERIC_ERROR'
    };
  }
}

/**
 * Validate ZIP file contents
 */
async function validateZipContents(buffer: Buffer): Promise<MimeValidationResult> {
  try {
    // Use JSZip to extract and validate entries
    const JSZip = (await import('jszip')).default;
    const zip = await JSZip.loadAsync(buffer);
    
    const entries = Object.keys(zip.files);
    
    if (entries.length === 0) {
      return {
        valid: false,
        error: 'ZIP file is empty',
        code: 'MALFORMED_FILE'
      };
    }
    
    // Check each entry
    for (const entry of entries) {
      if (zip.files[entry].dir) continue; // Skip directories
      
      const ext = entry.split('.').pop()?.toLowerCase();
      
      if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
        return {
          valid: false,
          error: `ZIP contains unsupported file: ${entry}`,
          code: 'ZIP_UNSUPPORTED_MIME'
        };
      }
    }
    
    return {
      valid: true,
      mime: 'application/zip'
    };
    
  } catch (error) {
    return {
      valid: false,
      error: 'Failed to validate ZIP contents',
      code: 'MALFORMED_FILE'
    };
  }
}

/**
 * Check if PDF is encrypted
 */
export async function isPDFEncrypted(buffer: Buffer): Promise<boolean> {
  try {
    // Use pdf-lib to check encryption
    const { PDFDocument } = await import('pdf-lib');
    
    try {
      // Try to load the PDF
      await PDFDocument.load(buffer, { ignoreEncryption: false });
      return false; // Not encrypted
    } catch (error: any) {
      // Check if error is due to encryption
      if (error.message?.includes('encrypted') || 
          error.message?.includes('password') ||
          error.message?.includes('Encryption')) {
        return true;
      }
      
      // Check PDF structure for /Encrypt keyword
      const pdfText = buffer.toString('latin1');
      if (pdfText.includes('/Encrypt')) {
        return true;
      }
      
      return false;
    }
  } catch (error) {
    console.error('PDF encryption check error:', error);
    // Fallback to basic check
    const pdfText = buffer.toString('latin1');
    return pdfText.includes('/Encrypt');
  }
}

