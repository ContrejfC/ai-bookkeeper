import { MetadataRoute } from 'next';
import { getActiveBanks, toRouteSlug } from '@/lib/pse-banks';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://ai-bookkeeper.app';

  const core: MetadataRoute.Sitemap = [
    { url: `${base}/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 1.0 },
    { url: `${base}/free/categorizer`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/gpt-bridge`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/tools/csv-cleaner`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/pricing`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.9 },
    { url: `${base}/privacy`, lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
    { url: `${base}/terms`, lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
    { url: `${base}/dpa`, lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
    { url: `${base}/security`, lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
  ];

  const guides: MetadataRoute.Sitemap = getActiveBanks().map(b => ({
    url: `${base}/guides/${toRouteSlug(b.slug)}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: b.priority || 0.8,
  }));

  return [...core, ...guides];
}
