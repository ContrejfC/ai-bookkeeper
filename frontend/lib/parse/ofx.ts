/**
 * OFX Parser
 * ===========
 * Parse Open Financial Exchange format to normalized transactions
 */

import type { Transaction } from './schema';
import { v4 as uuidv4 } from 'uuid';

/**
 * Parse OFX content to transactions
 */
export function parseOFX(content: string): Transaction[] {
  const transactions: Transaction[] = [];
  
  // OFX uses SGML-like tags
  // Example: <STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20250115<TRNAMT>-45.67<NAME>COFFEE SHOP<MEMO>Purchase
  
  const stmtTrnRegex = /<STMTTRN>([\s\S]*?)<\/STMTTRN>/gi;
  const matches = content.matchAll(stmtTrnRegex);
  
  let index = 0;
  for (const match of matches) {
    const block = match[1];
    
    // Extract fields
    const dateMatch = block.match(/<DTPOSTED>(\d{8})/);
    const amountMatch = block.match(/<TRNAMT>([-\d.]+)/);
    const nameMatch = block.match(/<NAME>([^<]+)/);
    const memoMatch = block.match(/<MEMO>([^<]+)/);
    const typeMatch = block.match(/<TRNTYPE>([^<]+)/);
    
    if (dateMatch && amountMatch) {
      const dateStr = dateMatch[1];
      const date = parseOFXDate(dateStr);
      const amount = parseFloat(amountMatch[1]);
      const name = nameMatch?.[1]?.trim() || '';
      const memo = memoMatch?.[1]?.trim() || '';
      const type = typeMatch?.[1]?.trim() || '';
      
      const description = [name, memo].filter(Boolean).join(' - ');
      
      transactions.push({
        id: uuidv4(),
        date,
        description: description || type,
        amount,
        rawDescription: description,
        rawAmount: amountMatch[1],
        originalIndex: index++,
      });
    }
  }
  
  return transactions;
}

/**
 * Parse OFX date format (YYYYMMDD or YYYYMMDDHHMMSS)
 */
function parseOFXDate(dateStr: string): Date {
  const year = parseInt(dateStr.substring(0, 4));
  const month = parseInt(dateStr.substring(4, 6)) - 1;
  const day = parseInt(dateStr.substring(6, 8));
  
  return new Date(year, month, day);
}

/**
 * Check if content is OFX format
 */
export function isOFX(content: string): boolean {
  return content.includes('<OFX>') || content.includes('<STMTTRN>');
}

