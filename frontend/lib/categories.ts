/**
 * QBO-Style Category List
 * ========================
 * Standard categories compatible with QuickBooks Online
 */

export interface Category {
  id: string;
  name: string;
  type: 'income' | 'expense' | 'other';
  qboClass?: string;
  keywords?: string[]; // For rule matching
}

export const QBO_CATEGORIES: Category[] = [
  // Income
  { id: 'income-sales', name: 'Sales Revenue', type: 'income', qboClass: 'Income', keywords: ['deposit', 'payment received', 'sales'] },
  { id: 'income-services', name: 'Service Revenue', type: 'income', qboClass: 'Income', keywords: ['consulting', 'services', 'fees earned'] },
  { id: 'income-interest', name: 'Interest Income', type: 'income', qboClass: 'Income', keywords: ['interest', 'dividend'] },
  { id: 'income-other', name: 'Other Income', type: 'income', qboClass: 'Income', keywords: ['refund', 'reimbursement'] },
  
  // Expenses - Operating
  { id: 'expense-advertising', name: 'Advertising & Marketing', type: 'expense', qboClass: 'Expense', keywords: ['google ads', 'facebook', 'marketing', 'advertising'] },
  { id: 'expense-auto', name: 'Auto & Vehicle', type: 'expense', qboClass: 'Expense', keywords: ['gas', 'fuel', 'parking', 'car', 'vehicle', 'uber', 'lyft'] },
  { id: 'expense-bank', name: 'Bank Fees & Charges', type: 'expense', qboClass: 'Expense', keywords: ['bank fee', 'service charge', 'overdraft'] },
  { id: 'expense-insurance', name: 'Insurance', type: 'expense', qboClass: 'Expense', keywords: ['insurance', 'premium'] },
  { id: 'expense-legal', name: 'Legal & Professional', type: 'expense', qboClass: 'Expense', keywords: ['lawyer', 'attorney', 'legal', 'consulting'] },
  { id: 'expense-meals', name: 'Meals & Entertainment', type: 'expense', qboClass: 'Expense', keywords: ['restaurant', 'coffee', 'starbucks', 'dinner', 'lunch'] },
  { id: 'expense-office', name: 'Office Supplies', type: 'expense', qboClass: 'Expense', keywords: ['staples', 'office depot', 'supplies', 'paper'] },
  { id: 'expense-rent', name: 'Rent & Lease', type: 'expense', qboClass: 'Expense', keywords: ['rent', 'lease'] },
  { id: 'expense-repairs', name: 'Repairs & Maintenance', type: 'expense', qboClass: 'Expense', keywords: ['repair', 'maintenance', 'fix'] },
  { id: 'expense-software', name: 'Software & Subscriptions', type: 'expense', qboClass: 'Expense', keywords: ['saas', 'software', 'subscription', 'hosting', 'aws', 'vercel'] },
  { id: 'expense-supplies', name: 'Supplies', type: 'expense', qboClass: 'Expense', keywords: ['supplies', 'materials'] },
  { id: 'expense-taxes', name: 'Taxes & Licenses', type: 'expense', qboClass: 'Expense', keywords: ['tax', 'irs', 'license', 'permit'] },
  { id: 'expense-travel', name: 'Travel', type: 'expense', qboClass: 'Expense', keywords: ['airline', 'hotel', 'travel', 'flight'] },
  { id: 'expense-utilities', name: 'Utilities', type: 'expense', qboClass: 'Expense', keywords: ['electric', 'gas', 'water', 'internet', 'phone', 'utility'] },
  { id: 'expense-wages', name: 'Wages & Payroll', type: 'expense', qboClass: 'Expense', keywords: ['payroll', 'salary', 'wages'] },
  
  // Common Expenses
  { id: 'expense-shipping', name: 'Shipping & Delivery', type: 'expense', qboClass: 'Expense', keywords: ['shipping', 'freight', 'ups', 'fedex', 'usps'] },
  { id: 'expense-postage', name: 'Postage', type: 'expense', qboClass: 'Expense', keywords: ['postage', 'stamps'] },
  { id: 'expense-dues', name: 'Dues & Subscriptions', type: 'expense', qboClass: 'Expense', keywords: ['membership', 'dues', 'subscription'] },
  
  // Other
  { id: 'other-transfer', name: 'Transfer', type: 'other', qboClass: 'Other', keywords: ['transfer', 'xfer'] },
  { id: 'other-payment', name: 'Payment', type: 'other', qboClass: 'Other', keywords: ['payment', 'pay'] },
  { id: 'uncategorized', name: 'Uncategorized', type: 'other', qboClass: 'Other', keywords: [] },
];

/**
 * Get category by ID
 */
export function getCategoryById(id: string): Category | undefined {
  return QBO_CATEGORIES.find(c => c.id === id);
}

/**
 * Get category by name
 */
export function getCategoryByName(name: string): Category | undefined {
  return QBO_CATEGORIES.find(c => c.name.toLowerCase() === name.toLowerCase());
}

/**
 * Get all expense categories
 */
export function getExpenseCategories(): Category[] {
  return QBO_CATEGORIES.filter(c => c.type === 'expense');
}

/**
 * Get all income categories
 */
export function getIncomeCategories(): Category[] {
  return QBO_CATEGORIES.filter(c => c.type === 'income');
}

/**
 * Get category names for dropdown
 */
export function getCategoryNames(): string[] {
  return QBO_CATEGORIES.map(c => c.name);
}

