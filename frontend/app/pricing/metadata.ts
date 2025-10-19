import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pricing - Plans Starting at $49/month | AI Bookkeeper',
  description: 'Choose the perfect AI bookkeeping plan for your business. Plans start at $49/month with 500 transactions. Starter, Team, Firm, and Enterprise options available.',
  openGraph: {
    title: 'Pricing - Plans Starting at $49/month',
    description: 'Choose the perfect AI bookkeeping plan for your business. Plans start at $49/month with 500 transactions.',
    url: 'https://app.ai-bookkeeper.app/pricing',
    siteName: 'AI Bookkeeper',
    images: [
      {
        url: 'https://app.ai-bookkeeper.app/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Pricing - Plans Starting at $49/month',
    description: 'Choose the perfect AI bookkeeping plan for your business. Plans start at $49/month.',
    images: ['https://app.ai-bookkeeper.app/og-image.png'],
  },
  alternates: {
    canonical: 'https://app.ai-bookkeeper.app/pricing',
  },
};

