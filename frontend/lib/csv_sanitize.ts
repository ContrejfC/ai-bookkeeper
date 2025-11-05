/**
 * CSV Formula Injection Prevention
 * =================================
 * 
 * Prevents formula injection attacks (CSV Injection) by prefixing
 * dangerous characters with a single quote when exporting CSVs.
 * 
 * Attack vectors:
 * - Cells starting with = (formulas)
 * - Cells starting with + (addition)
 * - Cells starting with - (subtraction)
 * - Cells starting with @ (indirect reference)
 * - Cells starting with \t or \r (tab/return injection)
 * 
 * Mitigation:
 * - Prefix with single quote (') to treat as text literal
 * - Preserves original for preview (user sees actual data)
 * - Sanitizes on download/export (safe for Excel/Sheets)
 */

const DANGEROUS_PREFIXES = ['=', '+', '-', '@', '\t', '\r'];

/**
 * Sanitize a single CSV field
 * 
 * @param value - The field value to sanitize
 * @returns Sanitized value with ' prefix if dangerous
 */
export function sanitizeCsvField(value: string | number | null | undefined): string {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return '';
  }
  
  // Convert to string
  const str = String(value);
  
  // Empty strings are safe
  if (str.length === 0) {
    return str;
  }
  
  // Check if starts with dangerous character
  const firstChar = str.charAt(0);
  if (DANGEROUS_PREFIXES.includes(firstChar)) {
    // Prefix with single quote to neutralize
    return `'${str}`;
  }
  
  return str;
}

/**
 * Sanitize an array of fields (single row)
 * 
 * @param row - Array of field values
 * @returns Sanitized row
 */
export function sanitizeCsvRow(row: (string | number | null | undefined)[]): string[] {
  return row.map(field => sanitizeCsvField(field));
}

/**
 * Sanitize a 2D array (full table)
 * 
 * @param rows - 2D array of rows and fields
 * @returns Sanitized table
 */
export function sanitizeCsvTable(rows: (string | number | null | undefined)[][]): string[][] {
  return rows.map(row => sanitizeCsvRow(row));
}

/**
 * Convert sanitized rows to CSV string
 * 
 * @param rows - Sanitized rows
 * @param includeHeader - Whether first row is header
 * @returns CSV string ready for download
 */
export function rowsToCsv(
  rows: string[][], 
  includeHeader: boolean = true
): string {
  return rows.map(row => 
    row.map(field => {
      // Quote fields that contain commas, quotes, or newlines
      if (field.includes(',') || field.includes('"') || field.includes('\n')) {
        return `"${field.replace(/"/g, '""')}"`;
      }
      return field;
    }).join(',')
  ).join('\n');
}

/**
 * Check if a value is potentially dangerous
 * 
 * @param value - Value to check
 * @returns True if value starts with dangerous character
 */
export function isDangerousValue(value: string | number | null | undefined): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  
  const str = String(value);
  if (str.length === 0) {
    return false;
  }
  
  return DANGEROUS_PREFIXES.includes(str.charAt(0));
}

/**
 * Get statistics about dangerous fields in a table
 * 
 * @param rows - 2D array of rows
 * @returns Count of dangerous fields
 */
export function getDangerousFieldCount(rows: (string | number | null | undefined)[][]): number {
  let count = 0;
  for (const row of rows) {
    for (const field of row) {
      if (isDangerousValue(field)) {
        count++;
      }
    }
  }
  return count;
}

