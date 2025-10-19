import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Run AI Bookkeeper in ChatGPT | AI Bookkeeper',
  description: 'Use our powerful AI bookkeeping assistant directly inside ChatGPT with GPT Actions. Automate your bookkeeping with AI.',
  openGraph: {
    title: 'Run AI Bookkeeper in ChatGPT',
    description: 'Use our powerful AI bookkeeping assistant directly inside ChatGPT with GPT Actions.',
    url: 'https://app.ai-bookkeeper.app/gpt-bridge',
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
    title: 'Run AI Bookkeeper in ChatGPT',
    description: 'Use our powerful AI bookkeeping assistant directly inside ChatGPT with GPT Actions.',
    images: ['https://app.ai-bookkeeper.app/og-image.png'],
  },
  alternates: {
    canonical: 'https://app.ai-bookkeeper.app/gpt-bridge',
  },
};

