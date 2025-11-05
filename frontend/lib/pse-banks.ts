import banks from '@/data/pse/banks.json';

export type Bank = { slug: string; name: string; active: boolean; priority?: number };
export const allBanks = (banks as Bank[]);

export const ROUTE_SUFFIX = '-export-csv';
export const toRouteSlug = (base: string) => `${base}${ROUTE_SUFFIX}`;
export const fromRouteSlug = (route: string) =>
  route.endsWith(ROUTE_SUFFIX) ? route.slice(0, -ROUTE_SUFFIX.length) : route;

export const getActiveBanks = () => allBanks.filter(b => b.active);
export const findBankByRouteSlug = (route: string) => {
  const base = fromRouteSlug(route);
  return allBanks.find(b => b.slug === base);
};
