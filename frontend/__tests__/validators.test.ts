/**
 * Unit Tests for Free Tool Validators
 * ===================================
 */

import { describe, it, expect } from '@jest/globals';
import { 
  validateExtension, 
  validateFileSize, 
  validateMimeType,
  checkPasswordProtectedPDF,
  validateFile,
  isValidEmail,
  sanitizeFilename
} from '../lib/validators';

describe('validators', () => {
  
  describe('validateExtension', () => {
    it('should accept valid CSV extension', () => {
      const result = validateExtension('statement.csv');
      expect(result.valid).toBe(true);
      expect(result.extension).toBe('csv');
    });

    it('should accept valid PDF extension', () => {
      const result = validateExtension('statement.pdf');
      expect(result.valid).toBe(true);
      expect(result.extension).toBe('pdf');
    });

    it('should reject invalid extension', () => {
      const result = validateExtension('statement.exe');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('not supported');
    });

    it('should reject file without extension', () => {
      const result = validateExtension('statement');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('no extension');
    });
  });

  describe('validateFileSize', () => {
    it('should accept CSV within size limit', () => {
      const result = validateFileSize(5 * 1024 * 1024, 'csv'); // 5MB
      expect(result.valid).toBe(true);
    });

    it('should reject oversized CSV', () => {
      const result = validateFileSize(15 * 1024 * 1024, 'csv'); // 15MB > 10MB limit
      expect(result.valid).toBe(false);
      expect(result.error).toContain('too large');
    });

    it('should accept PDF within size limit', () => {
      const result = validateFileSize(30 * 1024 * 1024, 'pdf'); // 30MB < 50MB limit
      expect(result.valid).toBe(true);
    });

    it('should reject oversized PDF', () => {
      const result = validateFileSize(60 * 1024 * 1024, 'pdf'); // 60MB > 50MB limit
      expect(result.valid).toBe(false);
    });
  });

  describe('validateMimeType', () => {
    it('should accept correct CSV mime type', () => {
      const result = validateMimeType('text/csv', 'csv');
      expect(result.valid).toBe(true);
    });

    it('should accept octet-stream as fallback', () => {
      const result = validateMimeType('application/octet-stream', 'csv');
      expect(result.valid).toBe(true);
    });

    it('should reject mismatched mime type', () => {
      const result = validateMimeType('image/jpeg', 'csv');
      expect(result.valid).toBe(false);
    });
  });

  describe('checkPasswordProtectedPDF', () => {
    it('should detect encrypted PDF', async () => {
      const encryptedContent = Buffer.from('...some binary data.../Encrypt...more data...');
      const result = await checkPasswordProtectedPDF(encryptedContent);
      expect(result).toBe(true);
    });

    it('should not flag unencrypted PDF', async () => {
      const normalContent = Buffer.from('...some binary data without encrypt...');
      const result = await checkPasswordProtectedPDF(normalContent);
      expect(result).toBe(false);
    });
  });

  describe('isValidEmail', () => {
    it('should accept valid email', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name+tag@example.co.uk')).toBe(true);
    });

    it('should reject invalid email', () => {
      expect(isValidEmail('notanemail')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
      expect(isValidEmail('test@')).toBe(false);
    });
  });

  describe('sanitizeFilename', () => {
    it('should remove special characters', () => {
      expect(sanitizeFilename('test<>file.csv')).toBe('test__file.csv');
      expect(sanitizeFilename('file|name?.pdf')).toBe('file_name_.pdf');
    });

    it('should truncate long filenames', () => {
      const longName = 'a'.repeat(300) + '.csv';
      const result = sanitizeFilename(longName);
      expect(result.length).toBeLessThanOrEqual(255);
    });
  });

  describe('validateFile - integration', () => {
    it('should validate valid CSV file', async () => {
      const file = {
        name: 'statement.csv',
        size: 5 * 1024 * 1024,
        type: 'text/csv'
      };
      
      const result = await validateFile(file);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should catch multiple errors', async () => {
      const file = {
        name: 'statement.exe',
        size: 500 * 1024 * 1024,
        type: 'application/x-msdownload'
      };
      
      const result = await validateFile(file);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
});

