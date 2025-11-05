/**
 * PSE Banks Data Loader
 * ======================
 * 
 * Helper functions to load and query bank guide data for programmatic SEO pages.
 */

import banksData from '@/data/pse/banks.json';

export interface BankFAQ {
  q: string;
  a: string;
}

export interface BankStep {
  title: string;
  body: string;
}

export interface BankNotes {
  quirks?: string[];
}

export interface BankRecord {
  id: string;
  bankSlug: string;
  bankName: string;
  formats: string[];
  primaryFormat: string;
  status: 'active' | 'noindex';
  priority: number;
  faq: BankFAQ[];
  steps: BankStep[];
  notes: BankNotes;
}

export interface BanksData {
  version: string;
  banks: BankRecord[];
}

/**
 * Get all bank records
 */
export function getAllBanks(): BankRecord[] {
  return (banksData as BanksData).banks;
}

/**
 * Get all active banks (for sitemap, lists)
 */
export function getActiveBanks(): BankRecord[] {
  return getAllBanks().filter(bank => bank.status === 'active');
}

/**
 * Find bank by slug
 */
export function getBankBySlug(slug: string): BankRecord | null {
  const bank = getAllBanks().find(b => b.bankSlug === slug);
  return bank || null;
}

/**
 * Generate all possible slugs (for static params in Next.js)
 */
export function getAllBankSlugs(): string[] {
  return getAllBanks().map(b => b.bankSlug);
}

/**
 * Get default export steps if bank doesn't have custom steps
 */
export function getDefaultExportSteps(bankName: string): BankStep[] {
  return [
    {
      title: 'Log in to online banking',
      body: `Visit your ${bankName} online banking portal and sign in with your credentials.`,
    },
    {
      title: 'Navigate to account activity',
      body: 'Select the account you want to export and go to the transactions or activity section.',
    },
    {
      title: 'Select date range',
      body: 'Choose the date range for the transactions you want to export (typically up to 18 months).',
    },
    {
      title: 'Download transactions',
      body: 'Click the Download, Export, or similar button and select CSV as the file format.',
    },
    {
      title: 'Save and categorize',
      body: 'Save the CSV file to your computer, then upload it to our free categorizer tool for instant organization.',
    },
  ];
}

/**
 * Get default FAQ if bank doesn't have custom FAQ
 */
export function getDefaultFAQ(bankName: string): BankFAQ[] {
  return [
    {
      q: `How do I export ${bankName} transactions to CSV?`,
      a: `Log in to ${bankName} online banking, navigate to your account activity, select your date range, then download transactions in CSV format.`,
    },
    {
      q: `Can I export business account transactions from ${bankName}?`,
      a: `Yes, most ${bankName} business accounts support CSV transaction exports through the business banking portal.`,
    },
    {
      q: `How far back can I download ${bankName} transactions?`,
      a: `${bankName} typically allows transaction exports for up to 12-18 months, though this may vary by account type.`,
    },
    {
      q: `What file formats does ${bankName} support?`,
      a: `${bankName} generally supports CSV, OFX, and QFX formats for exporting transaction data to accounting software.`,
    },
  ];
}

