/**
 * Error Codes and Repair Tips for Free Categorizer
 * ================================================
 * 
 * Typed error codes with friendly repair messages.
 */

export type ErrorCode =
  | 'ROW_LIMIT_EXCEEDED'
  | 'FILE_TOO_LARGE'
  | 'UNSUPPORTED_TYPE'
  | 'ZIP_UNSUPPORTED_MIME'
  | 'ZIP_SAFETY_VIOLATION'
  | 'MALFORMED_FILE'
  | 'ENCRYPTED_PDF'
  | 'PARSE_TIMEOUT'
  | 'CONSENT_REQUIRED'
  | 'EMAIL_INVALID'
  | 'RATE_LIMIT_EXCEEDED'
  | 'TOKEN_INVALID'
  | 'CODE_EXPIRED'
  | 'GENERIC_ERROR';

export interface FreeToolError {
  code: ErrorCode;
  message: string;
  repairTips: string[];
  helpLink?: string;
}

/**
 * Get error details for a given error code
 */
export function getErrorDetails(
  code: ErrorCode,
  context: Record<string, any> = {}
): FreeToolError {
  const { rows, maxRows, fileSizeMB, maxFileMB } = context;
  
  const errors: Record<ErrorCode, FreeToolError> = {
    ROW_LIMIT_EXCEEDED: {
      code: 'ROW_LIMIT_EXCEEDED',
      message: `Your file has ${rows || '?'} rows. The free limit is ${maxRows || 500}.`,
      repairTips: [
        'Try a smaller file with fewer transactions',
        'Split your file into multiple smaller files',
        'Upgrade to a paid plan for unlimited rows'
      ],
      helpLink: '/pricing'
    },
    
    FILE_TOO_LARGE: {
      code: 'FILE_TOO_LARGE',
      message: `File exceeds ${maxFileMB || 10} MB limit (${fileSizeMB?.toFixed(1) || '?'} MB uploaded).`,
      repairTips: [
        'Compress the file or reduce the date range',
        'Export a shorter time period from your bank',
        'Remove any embedded images or unnecessary data'
      ]
    },
    
    UNSUPPORTED_TYPE: {
      code: 'UNSUPPORTED_TYPE',
      message: 'Unsupported file format.',
      repairTips: [
        'Supported formats: CSV, OFX, QFX, PDF, JPG, PNG, ZIP',
        'Export a CSV or OFX file from your bank or accounting software',
        'Convert the file to a supported format'
      ],
      helpLink: '#help-export'
    },
    
    ZIP_UNSUPPORTED_MIME: {
      code: 'ZIP_UNSUPPORTED_MIME',
      message: 'ZIP contains unsupported or mixed file formats.',
      repairTips: [
        'Ensure all files in the ZIP are CSV, OFX, QFX, PDF, JPG, or PNG',
        'Remove any unsupported files from the archive',
        'Extract and upload files individually'
      ]
    },
    
    ZIP_SAFETY_VIOLATION: {
      code: 'ZIP_SAFETY_VIOLATION',
      message: 'ZIP file failed safety checks (too large, nested archives, or unsafe paths).',
      repairTips: [
        'Ensure total uncompressed size is under 50MB',
        'Remove nested ZIP/archive files',
        'Ensure file paths don't contain ../ or absolute paths',
        'Limit to 500 files per ZIP',
        'Extract and upload files individually instead'
      ],
      helpLink: '#help-zip-safety'
    },
    
    MALFORMED_FILE: {
      code: 'MALFORMED_FILE',
      message: 'The file could not be parsed. It may be corrupted or improperly formatted.',
      repairTips: [
        'Re-export a clean CSV/OFX/QFX file from your bank',
        'Ensure the file has proper headers and data',
        'Open the file in Excel/Numbers and check for formatting issues',
        'Try uploading the original file from your bank without modifications'
      ],
      helpLink: '#help-export'
    },
    
    ENCRYPTED_PDF: {
      code: 'ENCRYPTED_PDF',
      message: 'Password-protected PDFs are not supported.',
      repairTips: [
        'Remove the password protection from the PDF',
        'Print the PDF to a new PDF without password',
        'Export a CSV or OFX file instead'
      ]
    },
    
    PARSE_TIMEOUT: {
      code: 'PARSE_TIMEOUT',
      message: 'File parsing took too long and timed out.',
      repairTips: [
        'Try a smaller file or shorter date range',
        'Export a simpler format (CSV instead of PDF)',
        'Ensure the file is not corrupted',
        'Try again in a few moments'
      ]
    },
    
    CONSENT_REQUIRED: {
      code: 'CONSENT_REQUIRED',
      message: 'You must agree to the terms to proceed.',
      repairTips: [
        'Check the consent checkbox before downloading',
        'Review our Privacy Policy and Terms of Service'
      ],
      helpLink: '/privacy'
    },
    
    EMAIL_INVALID: {
      code: 'EMAIL_INVALID',
      message: 'Please enter a valid email address.',
      repairTips: [
        'Check for typos in your email address',
        'Ensure the email format is correct (e.g., name@example.com)',
        'Use a different email if this one is blocked'
      ]
    },
    
    RATE_LIMIT_EXCEEDED: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'You have exceeded the rate limit. Please try again later.',
      repairTips: [
        'Wait a few minutes before trying again',
        'The free tool has limits to prevent abuse',
        'Sign up for an account for higher limits'
      ],
      helpLink: '/signup'
    },
    
    TOKEN_INVALID: {
      code: 'TOKEN_INVALID',
      message: 'Invalid or expired verification token.',
      repairTips: [
        'Request a new verification code',
        'Check your email for the most recent code',
        'Ensure you are using the correct email address'
      ]
    },
    
    CODE_EXPIRED: {
      code: 'CODE_EXPIRED',
      message: 'Verification code expired or not found.',
      repairTips: [
        'Codes expire after 15 minutes',
        'Request a new code and verify promptly',
        'Check your spam/junk folder for the email'
      ]
    },
    
    GENERIC_ERROR: {
      code: 'GENERIC_ERROR',
      message: 'An unexpected error occurred. Please try again.',
      repairTips: [
        'Refresh the page and try again',
        'Clear your browser cache and cookies',
        'Try a different browser or device',
        'Contact support if the problem persists'
      ],
      helpLink: 'mailto:support@ai-bookkeeper.app'
    }
  };
  
  return errors[code] || errors.GENERIC_ERROR;
}

/**
 * Format error for display
 */
export function formatError(error: FreeToolError): string {
  return `${error.message}\n\nHow to fix:\n${error.repairTips.map((tip, i) => `${i + 1}. ${tip}`).join('\n')}`;
}

