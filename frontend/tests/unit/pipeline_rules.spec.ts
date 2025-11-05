/**
 * Pipeline and Rules Tests
 * =========================
 * Test categorization pipeline and rule matching
 */

import { describe, it, expect } from '@jest/globals';
import { applyRules, suggestRuleFromEdit, BUILTIN_RULES } from '@/lib/categorize/rules';
import { categorizeTransactions } from '@/lib/categorize/pipeline';
import type { Transaction } from '@/lib/parse/schema';

describe('Rules Engine', () => {
  it('should match coffee shop transactions', () => {
    const txn: Transaction = {
      id: '1',
      date: new Date('2025-01-15'),
      description: 'STARBUCKS COFFEE #12345',
      amount: -4.75,
    };

    const result = applyRules(txn);
    
    expect(result).toBeTruthy();
    expect(result?.category).toBe('Meals & Entertainment');
    expect(result?.explanation.confidence).toBe(0.95);
    expect(result?.explanation.stage).toBe('rule');
    expect(result?.explanation.ruleId).toBe('r-coffee');
  });

  it('should match fuel stations', () => {
    const txn: Transaction = {
      id: '2',
      date: new Date('2025-01-16'),
      description: 'SHELL OIL 76543',
      amount: -52.00,
    };

    const result = applyRules(txn);
    
    expect(result).toBeTruthy();
    expect(result?.category).toBe('Auto & Vehicle');
    expect(result?.explanation.ruleId).toBe('r-fuel');
  });

  it('should match SaaS providers', () => {
    const txn: Transaction = {
      id: '3',
      date: new Date('2025-01-17'),
      description: 'VERCEL INC',
      amount: -20.00,
    };

    const result = applyRules(txn);
    
    expect(result?.category).toBe('Software & Subscriptions');
  });

  it('should not match unrecognized merchants', () => {
    const txn: Transaction = {
      id: '4',
      date: new Date('2025-01-18'),
      description: 'UNKNOWN MERCHANT XYZ',
      amount: -100.00,
    };

    const result = applyRules(txn);
    expect(result).toBeNull();
  });

  it('should suggest rule from edit', () => {
    const txn: Transaction = {
      id: '5',
      date: new Date('2025-01-19'),
      description: 'ACME OFFICE SUPPLIES',
      amount: -67.43,
    };

    const rule = suggestRuleFromEdit(txn, 'Office Supplies');
    
    expect(rule.category).toBe('Office Supplies');
    expect(rule.priority).toBe(1); // User rules have highest priority
    expect(rule.descriptionContains).toBe('acme');
  });

  it('should prioritize user rules over built-in rules', () => {
    const txn: Transaction = {
      id: '6',
      date: new Date('2025-01-20'),
      description: 'STARBUCKS',
      amount: -5.00,
    };

    const userRule = {
      id: 'user-1',
      name: 'My Starbucks Rule',
      category: 'Personal Expense',
      priority: 1,
      merchantRegex: /starbucks/i,
    };

    const result = applyRules(txn, [userRule]);
    
    expect(result?.category).toBe('Personal Expense');
    expect(result?.explanation.ruleId).toBe('user-1');
  });
});

describe('Categorization Pipeline', () => {
  it('should categorize mixed transactions', async () => {
    const transactions: Transaction[] = [
      { id: '1', date: new Date(), description: 'STARBUCKS', amount: -4.50 },
      { id: '2', date: new Date(), description: 'SHELL GAS', amount: -45.00 },
      { id: '3', date: new Date(), description: 'UNKNOWN VENDOR', amount: -100.00 },
    ];

    const categorized = await categorizeTransactions(transactions);

    expect(categorized[0].category).toBe('Meals & Entertainment');
    expect(categorized[0].source).toBe('rule');
    expect(categorized[0].confidence).toBe(0.95);

    expect(categorized[1].category).toBe('Auto & Vehicle');
    expect(categorized[1].source).toBe('rule');

    // Unknown should get embedding or uncategorized
    expect(categorized[2].category).toBeDefined();
    expect(categorized[2].needsReview).toBe(true);
  });
});

