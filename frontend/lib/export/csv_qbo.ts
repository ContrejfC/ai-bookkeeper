/**
 * QuickBooks CSV Export
 * ======================
 * Export transactions in QuickBooks-friendly format
 */

import type { Transaction } from '../parse/schema';
import { sanitizeCsvTable } from '../csv_sanitize';

/**
 * Export transactions to QBO CSV format
 */
export function exportQBOCSV(transactions: Transaction[]): string {
  const headers = [
    'Date',
    'Description',
    'Amount',
    'Category',
    'Payee',
    'Class',
    'Location',
    'Memo',
  ];
  
  const rows = transactions.map(t => [
    t.date.toISOString().split('T')[0],
    t.description,
    t.amount.toFixed(2),
    t.category || 'Uncategorized',
    t.payee || extractPayeeFromDescription(t.description),
    '', // Class (empty for free tier)
    '', // Location (empty for free tier)
    buildMemo(t),
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

/**
 * Extract payee from description (first 30 chars)
 */
function extractPayeeFromDescription(description: string): string {
  return description.split(/\s+/).slice(0, 3).join(' ').substring(0, 30);
}

/**
 * Build memo field with confidence and source info
 */
function buildMemo(t: Transaction): string {
  const parts: string[] = [];
  
  if (t.confidence) {
    parts.push(`Confidence: ${(t.confidence * 100).toFixed(0)}%`);
  }
  
  if (t.source) {
    parts.push(`Source: ${t.source}`);
  }
  
  if (t.duplicate) {
    parts.push('Possible duplicate');
  }
  
  return parts.join(' | ');
}

