/**
 * Rule-Based Categorization Engine
 * ==================================
 * Merchant matching rules with regex support
 */

import type { Transaction, Explanation } from '../parse/schema';

export interface Rule {
  id: string;
  name: string;
  category: string;
  priority: number; // Lower = higher priority
  
  // Matching conditions (at least one must be specified)
  merchantRegex?: RegExp;
  descriptionContains?: string;
  amountMin?: number;
  amountMax?: number;
  isDebit?: boolean;  // true = negative amount
  isCredit?: boolean; // true = positive amount
}

// Built-in merchant rules
export const BUILTIN_RULES: Rule[] = [
  // Coffee & Food
  { id: 'r-coffee', name: 'Coffee Shops', category: 'Meals & Entertainment', priority: 10,
    merchantRegex: /starbucks|coffee|cafe|dunkin/i },
  { id: 'r-restaurant', name: 'Restaurants', category: 'Meals & Entertainment', priority: 11,
    descriptionContains: 'restaurant' },
  
  // Fuel & Auto
  { id: 'r-fuel', name: 'Gas Stations', category: 'Auto & Vehicle', priority: 10,
    merchantRegex: /shell|chevron|exxon|mobil|bp|arco|fuel|gas station/i },
  { id: 'r-uber', name: 'Ride Share', category: 'Auto & Vehicle', priority: 10,
    merchantRegex: /uber|lyft/i },
  
  // Office & Supplies
  { id: 'r-office', name: 'Office Supplies', category: 'Office Supplies', priority: 10,
    merchantRegex: /staples|office depot|amazon.*office/i },
  
  // Software & Cloud
  { id: 'r-saas', name: 'SaaS', category: 'Software & Subscriptions', priority: 10,
    merchantRegex: /vercel|aws|digitalocean|heroku|stripe|github/i },
  { id: 'r-hosting', name: 'Hosting', category: 'Software & Subscriptions', priority: 11,
    descriptionContains: 'hosting' },
  
  // Utilities
  { id: 'r-internet', name: 'Internet', category: 'Utilities', priority: 10,
    merchantRegex: /comcast|xfinity|att|verizon|spectrum/i },
  
  // Bank Fees
  { id: 'r-bank-fee', name: 'Bank Fees', category: 'Bank Fees & Charges', priority: 5,
    merchantRegex: /bank fee|service charge|monthly fee|overdraft/i },
  
  // Transfers (neutral)
  { id: 'r-transfer', name: 'Transfers', category: 'Transfer', priority: 15,
    merchantRegex: /transfer|xfer|trnsfr/i },
  
  // Payments
  { id: 'r-payment', name: 'Payment', category: 'Payment', priority: 16,
    descriptionContains: 'payment' },
];

/**
 * Apply rules to a transaction
 * Returns category and explanation if match found
 */
export function applyRules(
  txn: Transaction,
  customRules: Rule[] = []
): { category: string; explanation: Explanation } | null {
  const allRules = [...customRules, ...BUILTIN_RULES].sort((a, b) => a.priority - b.priority);
  
  const t0 = Date.now();
  
  for (const rule of allRules) {
    if (ruleMatches(rule, txn)) {
      return {
        category: rule.category,
        explanation: {
          stage: 'rule',
          confidence: 0.95,
          ruleId: rule.id,
          ruleName: rule.name,
          pipelineTimeMs: Date.now() - t0,
        },
      };
    }
  }
  
  return null;
}

/**
 * Check if a rule matches a transaction
 */
function ruleMatches(rule: Rule, txn: Transaction): boolean {
  // Check merchant regex
  if (rule.merchantRegex) {
    if (!rule.merchantRegex.test(txn.description)) {
      return false;
    }
  }
  
  // Check description contains
  if (rule.descriptionContains) {
    if (!txn.description.toLowerCase().includes(rule.descriptionContains.toLowerCase())) {
      return false;
    }
  }
  
  // Check amount range
  if (rule.amountMin !== undefined && Math.abs(txn.amount) < rule.amountMin) {
    return false;
  }
  if (rule.amountMax !== undefined && Math.abs(txn.amount) > rule.amountMax) {
    return false;
  }
  
  // Check debit/credit
  if (rule.isDebit && txn.amount >= 0) {
    return false;
  }
  if (rule.isCredit && txn.amount < 0) {
    return false;
  }
  
  return true;
}

/**
 * Create rule from user edit
 * Suggests a pattern based on the description
 */
export function suggestRuleFromEdit(
  txn: Transaction,
  category: string
): Rule {
  // Extract common token from description (first word, or most significant word)
  const words = txn.description.split(/\s+/).filter(w => w.length > 3);
  const token = words[0] || txn.description;
  
  return {
    id: `user-${Date.now()}`,
    name: `Auto: ${token}`,
    category,
    priority: 1, // User rules have highest priority
    descriptionContains: token.toLowerCase(),
  };
}

