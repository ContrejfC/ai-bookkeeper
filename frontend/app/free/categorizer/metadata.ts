/**
 * SEO Metadata for Free Categorizer
 * ==================================
 */

import { Metadata } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper-nine.vercel.app';

export const metadata: Metadata = {
  title: 'Free Bank Transaction Categorizer | CSV, OFX, QFX',
  description: 'Upload CSV, OFX, or QFX. Auto-categorize transactions, preview and download a clean CSV, or export to QuickBooks. Free tool with 24-hour deletion and opt-in training.',
  
  alternates: {
    canonical: `${SITE_URL}/free/categorizer`,
  },
  
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
  
  openGraph: {
    title: 'Free Bank Transaction Categorizer | CSV, OFX, QFX',
    description: 'Upload CSV, OFX, or QFX. Auto-categorize transactions, preview and download a clean CSV, or export to QuickBooks. Free tool with 24-hour deletion and opt-in training.',
    url: `${SITE_URL}/free/categorizer`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/api/og/free-categorizer`,
        width: 1200,
        height: 630,
        alt: 'AI Bookkeeper - Free Bank Transaction Categorizer',
      },
    ],
    siteName: 'AI Bookkeeper',
  },
  
  twitter: {
    card: 'summary_large_image',
    title: 'Free Bank Transaction Categorizer | CSV, OFX, QFX',
    description: 'Upload CSV, OFX, or QFX. Auto-categorize transactions, preview and download a clean CSV, or export to QuickBooks. Free tool with 24-hour deletion.',
    images: [`${SITE_URL}/api/og/free-categorizer`],
  },
  
  other: {
    'og:locale': 'en_US',
  },
};

