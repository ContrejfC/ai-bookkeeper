/**
 * Simple CSV Export
 * ==================
 * Export transactions to simple CSV format with all fields
 */

import type { Transaction } from '../parse/schema';
import { sanitizeCsvTable } from '../csv_sanitize';

/**
 * Export transactions to simple CSV format
 */
export function exportSimpleCSV(transactions: Transaction[]): string {
  const headers = [
    'Date',
    'Description',
    'Amount',
    'Category',
    'Confidence',
    'Source',
    'Duplicate',
    'Notes',
  ];
  
  const rows = transactions.map(t => [
    t.date.toISOString().split('T')[0],
    t.description,
    t.amount.toFixed(2),
    t.category || 'Uncategorized',
    t.confidence?.toFixed(2) || '',
    t.source || '',
    t.duplicate ? 'Yes' : 'No',
    t.explanation?.ruleName || t.explanation?.topMatch || '',
  ]);
  
  // Sanitize for formula injection
  const sanitized = sanitizeCsvTable([headers, ...rows]);
  
  // Convert to CSV string
  return sanitized.map(row =>
    row.map(cell => {
      // Quote cells with commas, quotes, or newlines
      if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    }).join(',')
  ).join('\n');
}

