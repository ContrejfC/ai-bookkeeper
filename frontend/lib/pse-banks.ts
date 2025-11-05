/**
 * PSE Banks Data Loader
 * ======================
 * 
 * Helper functions to load and query bank guide data for programmatic SEO pages.
 * Uses simplified data structure with slug computation helpers.
 */

import banksData from '@/data/pse/banks.json';

export interface Bank {
  slug: string;          // e.g., "chase"
  name: string;          // "Chase"
  active: boolean;       // true = indexable, false = noindex
  updatedAt?: string;    // ISO timestamp
  priority?: number;     // 0.0-1.0
}

interface BanksDataFile {
  version: string;
  banks: Array<{
    id: string;
    bankSlug: string;
    bankName: string;
    status: 'active' | 'noindex';
    priority: number;
    formats: string[];
    primaryFormat: string;
    faq: Array<{ q: string; a: string }>;
    steps: Array<{ title: string; body: string }>;
    notes: { quirks?: string[] };
  }>;
}

export const ROUTE_SUFFIX = '-export-csv';

/**
 * Get all banks with normalized structure
 */
export function getAllBanks(): Bank[] {
  const data = banksData as BanksDataFile;
  return data.banks.map(b => ({
    slug: b.id,
    name: b.bankName,
    active: b.status === 'active',
    priority: b.priority,
    updatedAt: undefined, // Can be added to JSON later
  }));
}

/**
 * Convert base slug to route slug
 * @param slugBase - Base slug like "chase"
 * @returns Route slug like "chase-export-csv"
 */
export function toRouteSlug(slugBase: string): string {
  return `${slugBase}${ROUTE_SUFFIX}`;
}

/**
 * Extract base slug from route slug
 * @param routeSlug - Route slug like "chase-export-csv"
 * @returns Base slug like "chase" or null if invalid
 */
export function fromRouteSlug(routeSlug: string): string | null {
  return routeSlug.endsWith(ROUTE_SUFFIX)
    ? routeSlug.slice(0, -ROUTE_SUFFIX.length)
    : null;
}

/**
 * Get all active banks with route slugs
 */
export function getActiveBanks(): Array<Bank & { routeSlug: string }> {
  return getAllBanks()
    .filter(b => b.active)
    .map(b => ({ ...b, routeSlug: toRouteSlug(b.slug) }));
}

/**
 * Find bank by route slug
 * @param routeSlug - Route slug like "chase-export-csv"
 * @returns Bank or null
 */
export function findBankByRouteSlug(routeSlug: string): Bank | null {
  const base = fromRouteSlug(routeSlug);
  if (!base) return null;
  const bank = getAllBanks().find(x => x.slug === base);
  return bank ?? null;
}

/**
 * Get bank raw data for detailed content (FAQ, steps, etc.)
 */
export function getBankDetails(slugBase: string) {
  const data = banksData as BanksDataFile;
  return data.banks.find(b => b.id === slugBase);
}
