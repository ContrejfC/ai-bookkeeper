/**
 * CSV Export Tests
 * ==================
 * Test export formats and formula injection prevention
 */

import { describe, it, expect } from '@jest/globals';
import { exportSimpleCSV } from '@/lib/export/csv_simple';
import { exportQBOCSV } from '@/lib/export/csv_qbo';
import { exportXeroCSV } from '@/lib/export/csv_xero';
import type { Transaction } from '@/lib/parse/schema';

describe('CSV Export', () => {
  const sampleTransactions: Transaction[] = [
    {
      id: '1',
      date: new Date('2025-01-15'),
      description: 'COFFEE SHOP',
      amount: -4.50,
      category: 'Meals & Entertainment',
      confidence: 0.95,
      source: 'rule',
      duplicate: false,
    },
    {
      id: '2',
      date: new Date('2025-01-16'),
      description: 'CLIENT PAYMENT',
      amount: 2500.00,
      category: 'Sales Revenue',
      confidence: 0.90,
      source: 'embedding',
      duplicate: false,
    },
  ];

  describe('exportSimpleCSV', () => {
    it('should export with all columns', () => {
      const csv = exportSimpleCSV(sampleTransactions);
      
      expect(csv).toContain('Date,Description,Amount,Category');
      expect(csv).toContain('2025-01-15');
      expect(csv).toContain('COFFEE SHOP');
      expect(csv).toContain('-4.50');
      expect(csv).toContain('Meals & Entertainment');
    });

    it('should include confidence and source', () => {
      const csv = exportSimpleCSV(sampleTransactions);
      
      expect(csv).toContain('0.95');
      expect(csv).toContain('rule');
    });
  });

  describe('exportQBOCSV', () => {
    it('should export in QBO format', () => {
      const csv = exportQBOCSV(sampleTransactions);
      
      expect(csv).toContain('Date,Description,Amount,Category,Payee');
      expect(csv).toContain('2025-01-15');
      expect(csv).toContain('COFFEE SHOP');
    });
  });

  describe('exportXeroCSV', () => {
    it('should export in Xero format', () => {
      const csv = exportXeroCSV(sampleTransactions);
      
      expect(csv).toContain('*Date,*Amount');
      expect(csv).toContain('2025-01-15');
      expect(csv).toContain('-4.50');
    });
  });

  describe('Formula Injection Prevention', () => {
    it('should sanitize cells starting with =', () => {
      const malicious: Transaction[] = [
        {
          id: '1',
          date: new Date('2025-01-15'),
          description: '=1+1',
          amount: -10.00,
          category: 'Test',
        },
      ];

      const csv = exportSimpleCSV(malicious);
      
      // Should be prefixed with '
      expect(csv).toContain("'=1+1");
      expect(csv).not.toMatch(/^=1\+1/m);
    });

    it('should sanitize cells starting with +', () => {
      const malicious: Transaction[] = [
        {
          id: '1',
          date: new Date('2025-01-15'),
          description: '+SUM(A1:A10)',
          amount: -10.00,
          category: 'Test',
        },
      ];

      const csv = exportSimpleCSV(malicious);
      expect(csv).toContain("'+SUM");
    });

    it('should sanitize cells starting with -', () => {
      const malicious: Transaction[] = [
        {
          id: '1',
          date: new Date('2025-01-15'),
          description: '-2+3',
          amount: -10.00,
          category: 'Test',
        },
      ];

      const csv = exportSimpleCSV(malicious);
      expect(csv).toContain("'-2+3");
    });

    it('should sanitize cells starting with @', () => {
      const malicious: Transaction[] = [
        {
          id: '1',
          date: new Date('2025-01-15'),
          description: '@cmd',
          amount: -10.00,
          category: 'Test',
        },
      ];

      const csv = exportSimpleCSV(malicious);
      expect(csv).toContain("'@cmd");
    });

    it('should work with all export formats', () => {
      const malicious: Transaction[] = [
        {
          id: '1',
          date: new Date('2025-01-15'),
          description: '=MALICIOUS',
          amount: -10.00,
          category: 'Test',
        },
      ];

      const simple = exportSimpleCSV(malicious);
      const qbo = exportQBOCSV(malicious);
      const xero = exportXeroCSV(malicious);

      expect(simple).toContain("'=");
      expect(qbo).toContain("'=");
      expect(xero).toContain("'=");
    });
  });
});

