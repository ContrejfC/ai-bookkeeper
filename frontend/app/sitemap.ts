import type { MetadataRoute } from 'next';
import { getActiveBanks, toRouteSlug } from '@/lib/pse-banks';

export default function sitemap(): MetadataRoute.Sitemap {
  const site = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app';
  const guides = getActiveBanks().map(b => ({
    url: `${site}/guides/${toRouteSlug(b.slug)}`,
    changeFrequency: 'monthly' as const,
    priority: b.priority ?? 0.7
  }));

  return [
    { url: `${site}/`, changeFrequency: 'monthly', priority: 1.0 },
    { url: `${site}/free/categorizer`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${site}/pricing`, changeFrequency: 'monthly', priority: 0.6 },
    { url: `${site}/privacy`, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${site}/terms`, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${site}/dpa`, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${site}/security`, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${site}/gpt-bridge`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${site}/tools/csv-cleaner`, changeFrequency: 'weekly', priority: 0.9 },
    ...guides
  ];
}
