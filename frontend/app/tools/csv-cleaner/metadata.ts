import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Free CSV Transaction Cleaner | AI Bookkeeper',
  description: 'Upload your bank statement CSV and get AI-powered transaction categorization instantly. Preview up to 50 rows for free with our CSV cleaner tool.',
  openGraph: {
    title: 'Free CSV Transaction Cleaner',
    description: 'Upload your bank statement CSV and get AI-powered transaction categorization instantly.',
    url: 'https://app.ai-bookkeeper.app/tools/csv-cleaner',
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
    title: 'Free CSV Transaction Cleaner',
    description: 'Upload your bank statement CSV and get AI-powered transaction categorization instantly.',
    images: ['https://app.ai-bookkeeper.app/og-image.png'],
  },
  alternates: {
    canonical: 'https://app.ai-bookkeeper.app/tools/csv-cleaner',
  },
};

