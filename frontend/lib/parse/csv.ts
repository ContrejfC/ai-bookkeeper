/**
 * CSV Parser with Auto-Detection
 * ================================
 * Parse CSV files with automatic column detection and deduplication
 */

import type { Transaction, ParsedData, ColumnMapping, CSVRow } from './schema';
import { detectColumns, detectDelimiter, detectDateFormat, parseDate, parseAmount } from './csv_detect';
import { v4 as uuidv4 } from 'uuid';
import { createHash } from 'crypto';

/**
 * Parse CSV content to transactions
 */
export function parseCSV(content: string): ParsedData {
  const delimiter = detectDelimiter(content);
  const lines = content.split('\n').filter(line => line.trim());
  
  if (lines.length < 2) {
    throw new Error('CSV must have at least a header and one data row');
  }
  
  // Parse header
  const headers = parseCSVLine(lines[0], delimiter);
  
  // Parse rows
  const rows: CSVRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i], delimiter);
    if (values.length > 0) {
      const row: CSVRow = {};
      headers.forEach((header, idx) => {
        row[header] = values[idx] || '';
      });
      rows.push(row);
    }
  }
  
  // Detect columns
  const columnMapping = detectColumns(headers, rows.slice(0, 10));
  
  // Convert to transactions
  const transactions = rowsToTransactions(rows, headers, columnMapping);
  
  // Detect duplicates
  markDuplicates(transactions);
  
  // Detect date format
  const dates = transactions
    .map(t => t.rawDescription?.match(/\d{1,2}\/\d{1,2}\/\d{4}/)?.[0])
    .filter(Boolean) as string[];
  const dateFormat = detectDateFormat(dates);
  
  return {
    transactions,
    columnMapping,
    rowCount: transactions.length,
    dateFormat,
    duplicateCount: transactions.filter(t => t.duplicate).length,
  };
}

/**
 * Parse a single CSV line respecting quotes
 */
function parseCSVLine(line: string, delimiter: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      // Handle escaped quotes
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++; // Skip next quote
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === delimiter && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  result.push(current.trim());
  return result;
}

/**
 * Convert CSV rows to transactions
 */
function rowsToTransactions(
  rows: CSVRow[],
  headers: string[],
  mapping: ColumnMapping
): Transaction[] {
  const transactions: Transaction[] = [];
  
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    
    // Extract date
    const dateStr = mapping.date !== undefined ? row[headers[mapping.date]] : '';
    const date = parseDate(dateStr);
    if (!date) continue; // Skip rows without valid dates
    
    // Extract description
    const description = mapping.description !== undefined
      ? row[headers[mapping.description]]?.trim()
      : '';
    
    // Extract amount
    let amount = 0;
    if (mapping.amount !== undefined) {
      amount = parseAmount(row[headers[mapping.amount]]);
    } else if (mapping.debit !== undefined && mapping.credit !== undefined) {
      const debit = parseAmount(row[headers[mapping.debit]]);
      const credit = parseAmount(row[headers[mapping.credit]]);
      amount = credit - debit; // Positive = credit, negative = debit
    }
    
    // Extract payee
    const payee = mapping.payee !== undefined
      ? row[headers[mapping.payee]]?.trim()
      : extractPayee(description);
    
    transactions.push({
      id: uuidv4(),
      date,
      description: description || 'Unknown',
      amount,
      payee,
      rawDescription: description,
      rawAmount: mapping.amount !== undefined ? row[headers[mapping.amount]] : `${amount}`,
      originalIndex: i,
    });
  }
  
  return transactions;
}

/**
 * Extract payee from description (simple heuristic)
 */
function extractPayee(description: string): string {
  // Take first 30 chars or until number/special char
  const payee = description.split(/\s+/).slice(0, 3).join(' ');
  return payee.substring(0, 30);
}

/**
 * Mark duplicate transactions
 * Hash based on: date±1day, normalized description, rounded amount
 */
function markDuplicates(transactions: Transaction[]): void {
  const seen = new Set<string>();
  
  for (const txn of transactions) {
    const hash = getDuplicateHash(txn);
    
    if (seen.has(hash)) {
      txn.duplicate = true;
    } else {
      seen.add(hash);
      
      // Also add hashes for ±1 day to catch near-duplicates
      const prevDayHash = getDuplicateHash(txn, -1);
      const nextDayHash = getDuplicateHash(txn, 1);
      seen.add(prevDayHash);
      seen.add(nextDayHash);
    }
  }
}

/**
 * Generate hash for duplicate detection
 */
function getDuplicateHash(txn: Transaction, dayOffset: number = 0): string {
  const date = new Date(txn.date);
  date.setDate(date.getDate() + dayOffset);
  const dateStr = date.toISOString().split('T')[0];
  
  // Normalize description: lowercase, remove special chars, collapse spaces
  const normalized = txn.description
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  
  // Round amount to nearest dollar
  const roundedAmount = Math.round(txn.amount);
  
  const hashInput = `${dateStr}|${normalized}|${roundedAmount}`;
  return createHash('md5').update(hashInput).digest('hex');
}

