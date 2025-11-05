/**
 * CSV Detection Tests
 * ====================
 */

import { describe, it, expect } from '@jest/globals';
import { detectColumns, parseDate, parseAmount, detectDelimiter } from '@/lib/parse/csv_detect';
import type { CSVRow } from '@/lib/parse/schema';

describe('CSV Detection', () => {
  describe('detectColumns', () => {
    it('should detect standard US format columns', () => {
      const headers = ['Date', 'Description', 'Amount'];
      const sampleRows: CSVRow[] = [
        { Date: '2025-01-15', Description: 'COFFEE SHOP', Amount: '-4.50' },
        { Date: '2025-01-16', Description: 'GAS STATION', Amount: '-52.00' },
      ];

      const mapping = detectColumns(headers, sampleRows);

      expect(mapping.date).toBe(0);
      expect(mapping.description).toBe(1);
      expect(mapping.amount).toBe(2);
    });

    it('should detect debit/credit columns', () => {
      const headers = ['Date', 'Details', 'Debit', 'Credit'];
      const sampleRows: CSVRow[] = [
        { Date: '2025-01-15', Details: 'OFFICE', Debit: '67.43', Credit: '' },
        { Date: '2025-01-16', Details: 'PAYMENT', Debit: '', Credit: '3000.00' },
      ];

      const mapping = detectColumns(headers, sampleRows);

      expect(mapping.date).toBe(0);
      expect(mapping.description).toBe(1);
      expect(mapping.debit).toBe(2);
      expect(mapping.credit).toBe(3);
    });
  });

  describe('parseDate', () => {
    it('should parse ISO dates', () => {
      const date = parseDate('2025-01-15');
      expect(date).toBeInstanceOf(Date);
      expect(date?.getFullYear()).toBe(2025);
      expect(date?.getMonth()).toBe(0); // January = 0
      expect(date?.getDate()).toBe(15);
    });

    it('should parse US format dates', () => {
      const date = parseDate('1/15/2025');
      expect(date).toBeInstanceOf(Date);
      expect(date?.getMonth()).toBe(0);
      expect(date?.getDate()).toBe(15);
    });

    it('should return null for invalid dates', () => {
      expect(parseDate('invalid')).toBeNull();
      expect(parseDate('')).toBeNull();
    });
  });

  describe('parseAmount', () => {
    it('should parse simple amounts', () => {
      expect(parseAmount('123.45')).toBe(123.45);
      expect(parseAmount('-67.89')).toBe(-67.89);
    });

    it('should handle currency symbols', () => {
      expect(parseAmount('$123.45')).toBe(123.45);
      expect(parseAmount('-$67.89')).toBe(-67.89);
    });

    it('should handle thousands separators', () => {
      expect(parseAmount('1,234.56')).toBe(1234.56);
      expect(parseAmount('$1,234.56')).toBe(1234.56);
    });
  });

  describe('detectDelimiter', () => {
    it('should detect comma delimiter', () => {
      const content = 'Date,Description,Amount\n2025-01-01,Test,-10.00';
      expect(detectDelimiter(content)).toBe(',');
    });

    it('should detect semicolon delimiter', () => {
      const content = 'Date;Description;Amount\n2025-01-01;Test;-10.00';
      expect(detectDelimiter(content)).toBe(';');
    });

    it('should detect tab delimiter', () => {
      const content = 'Date\tDescription\tAmount\n2025-01-01\tTest\t-10.00';
      expect(detectDelimiter(content)).toBe('\t');
    });
  });
});

