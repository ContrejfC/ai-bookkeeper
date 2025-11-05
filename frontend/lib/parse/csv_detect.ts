/**
 * CSV Column Detection
 * =====================
 * Auto-detect date, description, amount columns with multiple format support
 */

import type { ColumnMapping, CSVRow } from './schema';

const DATE_PATTERNS = [
  // ISO formats
  /^\d{4}-\d{2}-\d{2}$/,                           // 2025-01-15
  /^\d{4}\/\d{2}\/\d{2}$/,                         // 2025/01/15
  
  // US formats
  /^\d{1,2}\/\d{1,2}\/\d{4}$/,                     // 1/15/2025 or 01/15/2025
  /^\d{1,2}-\d{1,2}-\d{4}$/,                       // 1-15-2025
  
  // EU formats
  /^\d{1,2}\/\d{1,2}\/\d{4}$/,                     // 15/01/2025 (same as US, context matters)
  /^\d{1,2}\.\d{1,2}\.\d{4}$/,                     // 15.01.2025
  
  // Month names
  /^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,  // Jan 15, 2025
  /^\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i, // 15 Jan 2025
];

const AMOUNT_PATTERN = /^-?\$?\d{1,3}(,?\d{3})*(\.\d{2})?$/;

const COLUMN_NAME_HINTS = {
  date: ['date', 'posted', 'transaction date', 'trans date', 'value date'],
  description: ['description', 'memo', 'details', 'payee', 'merchant', 'narrative'],
  amount: ['amount', 'total', 'value'],
  debit: ['debit', 'withdrawal', 'withdrawals', 'payments'],
  credit: ['credit', 'deposit', 'deposits', 'credits'],
  payee: ['payee', 'vendor', 'merchant'],
};

/**
 * Detect column mapping from CSV headers and sample rows
 */
export function detectColumns(
  headers: string[],
  sampleRows: CSVRow[]
): ColumnMapping {
  const mapping: ColumnMapping = {};
  
  // Normalize headers
  const normalizedHeaders = headers.map(h => h.toLowerCase().trim());
  
  // 1. Try name-based detection first
  mapping.date = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.date);
  mapping.description = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.description);
  mapping.amount = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.amount);
  mapping.debit = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.debit);
  mapping.credit = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.credit);
  mapping.payee = findColumnByName(normalizedHeaders, COLUMN_NAME_HINTS.payee);
  
  // 2. Content-based detection if names failed
  if (sampleRows.length > 0) {
    if (mapping.date === undefined) {
      mapping.date = findDateColumn(headers, sampleRows);
    }
    
    if (mapping.amount === undefined && !mapping.debit && !mapping.credit) {
      mapping.amount = findAmountColumn(headers, sampleRows);
    }
    
    if (mapping.description === undefined) {
      mapping.description = findDescriptionColumn(headers, sampleRows, mapping);
    }
  }
  
  return mapping;
}

/**
 * Find column index by matching header names
 */
function findColumnByName(headers: string[], hints: string[]): number | undefined {
  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    for (const hint of hints) {
      if (header === hint || header.includes(hint)) {
        return i;
      }
    }
  }
  return undefined;
}

/**
 * Find date column by content analysis
 */
function findDateColumn(headers: string[], rows: CSVRow[]): number | undefined {
  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    let dateCount = 0;
    
    // Check first 5 rows
    for (let r = 0; r < Math.min(5, rows.length); r++) {
      const value = rows[r][header]?.trim();
      if (value && isDateLike(value)) {
        dateCount++;
      }
    }
    
    // If 80%+ look like dates, it's probably the date column
    if (dateCount >= Math.min(4, rows.length * 0.8)) {
      return i;
    }
  }
  
  return undefined;
}

/**
 * Find amount column by content analysis
 */
function findAmountColumn(headers: string[], rows: CSVRow[]): number | undefined {
  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    let amountCount = 0;
    
    // Check first 5 rows
    for (let r = 0; r < Math.min(5, rows.length); r++) {
      const value = rows[r][header]?.trim();
      if (value && isAmountLike(value)) {
        amountCount++;
      }
    }
    
    // If 80%+ look like amounts, it's probably the amount column
    if (amountCount >= Math.min(4, rows.length * 0.8)) {
      return i;
    }
  }
  
  return undefined;
}

/**
 * Find description column (usually longest text field)
 */
function findDescriptionColumn(
  headers: string[],
  rows: CSVRow[],
  mapping: ColumnMapping
): number | undefined {
  const excludeIndices = new Set([
    mapping.date,
    mapping.amount,
    mapping.debit,
    mapping.credit,
  ].filter(idx => idx !== undefined));
  
  let maxAvgLength = 0;
  let bestIndex: number | undefined;
  
  for (let i = 0; i < headers.length; i++) {
    if (excludeIndices.has(i)) continue;
    
    const header = headers[i];
    let totalLength = 0;
    let count = 0;
    
    for (let r = 0; r < Math.min(10, rows.length); r++) {
      const value = rows[r][header]?.trim();
      if (value) {
        totalLength += value.length;
        count++;
      }
    }
    
    const avgLength = count > 0 ? totalLength / count : 0;
    if (avgLength > maxAvgLength && avgLength > 10) {
      maxAvgLength = avgLength;
      bestIndex = i;
    }
  }
  
  return bestIndex;
}

/**
 * Check if value looks like a date
 */
function isDateLike(value: string): boolean {
  for (const pattern of DATE_PATTERNS) {
    if (pattern.test(value)) {
      return true;
    }
  }
  return false;
}

/**
 * Check if value looks like an amount
 */
function isAmountLike(value: string): boolean {
  return AMOUNT_PATTERN.test(value);
}

/**
 * Parse date string with multiple format support
 */
export function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  
  const trimmed = dateStr.trim();
  
  // Try ISO formats first
  const isoDate = new Date(trimmed);
  if (!isNaN(isoDate.getTime())) {
    return isoDate;
  }
  
  // Try US format: MM/DD/YYYY or M/D/YYYY
  const usMatch = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (usMatch) {
    const [, month, day, year] = usMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    if (!isNaN(date.getTime())) {
      return date;
    }
  }
  
  // Try EU format: DD/MM/YYYY or DD.MM.YYYY
  const euMatch = trimmed.match(/^(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{4})$/);
  if (euMatch) {
    const [, day, month, year] = euMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    if (!isNaN(date.getTime())) {
      // Disambiguate US vs EU by checking if day > 12
      if (parseInt(day) > 12) {
        return date; // Definitely EU format
      }
      // Otherwise, unclear - default to US format above
    }
  }
  
  return null;
}

/**
 * Parse amount string to number
 */
export function parseAmount(amountStr: string): number {
  if (!amountStr) return 0;
  
  // Remove currency symbols, commas, spaces
  const cleaned = amountStr
    .replace(/[$€£¥,\s]/g, '')
    .trim();
  
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

/**
 * Detect delimiter (comma, semicolon, tab)
 */
export function detectDelimiter(content: string): string {
  const firstLine = content.split('\n')[0];
  
  const counts = {
    ',': (firstLine.match(/,/g) || []).length,
    ';': (firstLine.match(/;/g) || []).length,
    '\t': (firstLine.match(/\t/g) || []).length,
  };
  
  // Return delimiter with highest count
  if (counts[';'] > counts[','] && counts[';'] > counts['\t']) {
    return ';';
  }
  if (counts['\t'] > counts[',']) {
    return '\t';
  }
  return ',';
}

/**
 * Detect date format from sample dates
 */
export function detectDateFormat(dates: string[]): string {
  const sample = dates.filter(d => d && d.trim()).slice(0, 5);
  
  if (sample.length === 0) return 'YYYY-MM-DD';
  
  // Check for ISO format
  if (sample.every(d => /^\d{4}[-\/]\d{2}[-\/]\d{2}$/.test(d))) {
    return 'YYYY-MM-DD';
  }
  
  // Check for month names
  if (sample.some(d => /jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/i.test(d))) {
    return 'MMM DD, YYYY';
  }
  
  // Check if any day > 12 (indicates EU format)
  for (const dateStr of sample) {
    const parts = dateStr.split(/[\/\-\.]/);
    if (parts.length === 3) {
      const first = parseInt(parts[0]);
      if (first > 12) {
        return 'DD/MM/YYYY'; // EU format
      }
    }
  }
  
  // Default to US format
  return 'MM/DD/YYYY';
}

