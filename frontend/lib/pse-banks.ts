/**
 * PSE Banks Helpers
 * ==================
 * Minimal helpers for bank guide route generation and lookup.
 */

export const ROUTE_SUFFIX = '-export-csv';

export const toRouteSlug = (s: string) => `${s}${ROUTE_SUFFIX}`;

export const fromRouteSlug = (r: string) =>
  r.endsWith(ROUTE_SUFFIX) ? r.slice(0, -ROUTE_SUFFIX.length) : null;

export type Bank = {
  slug: string;
  name: string;
  active: boolean;
  priority?: number;
};

let _banks: Bank[] | null = null;

export function getBanks(): Bank[] {
  if (!_banks) {
    _banks = require('../data/pse/banks.json');
  }
  return _banks!;
}

export function getActiveBanks(): Bank[] {
  return getBanks().filter(b => b.active);
}

export function findBankByRouteSlug(routeSlug: string): Bank | null {
  const base = fromRouteSlug(routeSlug);
  if (!base) return null;
  return getBanks().find(b => b.slug === base) ?? null;
}
