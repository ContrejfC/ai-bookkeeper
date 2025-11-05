/**
 * QFX Parser
 * ===========
 * Parse Quicken Financial Exchange format (variant of OFX)
 */

import type { Transaction } from './schema';
import { parseOFX, isOFX } from './ofx';

/**
 * Parse QFX content to transactions
 * QFX is essentially OFX with minor differences
 */
export function parseQFX(content: string): Transaction[] {
  // QFX uses same structure as OFX, just reuse parser
  return parseOFX(content);
}

/**
 * Check if content is QFX format
 */
export function isQFX(content: string): boolean {
  // QFX often has QFXHEADER or uses same OFX tags
  return content.includes('QFXHEADER') || isOFX(content);
}

