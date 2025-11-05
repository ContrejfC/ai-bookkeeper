/**
 * Xero CSV Export
 * =================
 * Export transactions in Xero-compatible format
 */

import type { Transaction } from '../parse/schema';
import { sanitizeCsvTable } from '../csv_sanitize';

/**
 * Export transactions to Xero CSV format
 */
export function exportXeroCSV(transactions: Transaction[]): string {
  const headers = [
    '*Date',
    '*Amount',
    'Payee',
    'Description',
    'Reference',
    'Check Number',
    'Account Code',
    'Tax Type',
    'Tax Amount',
    'Tracking Category 1',
    'Tracking Category 2',
  ];

  const rows = transactions.map(t => [
    t.date.toISOString().split('T')[0],
    t.amount.toFixed(2),
    t.payee || extractPayee(t.description),
    t.description,
    '', // Reference
    '', // Check Number
    t.category || 'Uncategorized',
    '', // Tax Type
    '', // Tax Amount
    '', // Tracking Category 1
    '', // Tracking Category 2
  ]);

  // Sanitize for formula injection
  const sanitized = sanitizeCsvTable([headers, ...rows]);

  // Convert to CSV string
  return sanitized.map(row =>
    row.map(cell => {
      if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    }).join(',')
  ).join('\n');
}

function extractPayee(description: string): string {
  return description.split(/\s+/).slice(0, 3).join(' ').substring(0, 30);
}

