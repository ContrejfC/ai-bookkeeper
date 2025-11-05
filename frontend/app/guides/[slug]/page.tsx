/**
 * Bank Export Guide - Dynamic Page
 * ==================================
 * 
 * Programmatic SEO pages for bank transaction export guides.
 * Only active banks are pre-built; noindex banks render on-demand.
 */

import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import { getActiveBanks, findBankByRouteSlug, getBankDetails } from '@/lib/pse-banks';

export const dynamic = 'error'; // Ensure SSG
export const revalidate = 86400; // Daily revalidation

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app';

// Generate static params ONLY for active banks
export async function generateStaticParams() {
  return getActiveBanks().map(b => ({ slug: b.routeSlug }));
}

// Generate metadata for each page
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const bank = findBankByRouteSlug(slug);
  
  if (!bank) {
    return { robots: { index: false, follow: true } };
  }

  const canonical = `${SITE_URL}/guides/${slug}`;
  const title = `${bank.name} — Export Transactions to CSV (Guide)`;
  const description = `Step-by-step: export ${bank.name} transactions to CSV. Then auto-categorize with the Free Categorizer.`;

  return {
    title,
    description,
    alternates: { canonical },
    robots: bank.active
      ? { index: true, follow: true }
      : { index: false, follow: true },
    openGraph: {
      title,
      description,
      url: canonical,
      images: [`${SITE_URL}/api/og/pse?slug=${encodeURIComponent(slug)}`],
      type: 'article',
      siteName: 'AI Bookkeeper',
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
    },
  };
}

// Page component
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const bank = findBankByRouteSlug(slug);
  
  if (!bank) {
    notFound();
  }

  // Get detailed data for steps and FAQ
  const details = getBankDetails(bank.slug);
  const steps = details?.steps || [
    { title: `Sign in to ${bank.name}`, body: `Visit your ${bank.name} online banking portal and sign in with your credentials.` },
    { title: 'Navigate to Transactions', body: 'Go to Transactions or Activity section.' },
    { title: 'Select date range', body: 'Choose the date range for transactions you want to export.' },
    { title: 'Export to CSV', body: 'Click Export or Download and select CSV format.' },
    { title: 'Use the Free Categorizer', body: 'Upload your CSV to our categorizer for instant organization.' },
  ];

  const faq = details?.faq || [
    {
      q: `How do I export ${bank.name} transactions to CSV?`,
      a: `Log in to ${bank.name} online banking, navigate to your account activity, select your date range, then download transactions in CSV format.`,
    },
    {
      q: `Can I export business account transactions from ${bank.name}?`,
      a: `Yes, most ${bank.name} business accounts support CSV transaction exports through the business banking portal.`,
    },
    {
      q: `How far back can I download ${bank.name} transactions?`,
      a: `${bank.name} typically allows transaction exports for up to 12-18 months, though this may vary by account type.`,
    },
  ];

  // JSON-LD: HowTo Schema
  const howToSchema = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: `How to export ${bank.name} transactions to CSV`,
    description: `Step-by-step guide to export ${bank.name} bank transactions to CSV format for categorization and accounting.`,
    step: steps.map((step, index) => ({
      '@type': 'HowToStep',
      position: index + 1,
      name: step.title,
      text: step.body,
    })),
  };

  // JSON-LD: FAQPage Schema
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map(item => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  };

  return (
    <>
      {/* JSON-LD Schemas */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />

      {/* Page Content */}
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-bold mb-2">
          {bank.name}: Export Transactions to CSV
        </h1>
        <p className="text-gray-600 mb-6">
          Follow these steps to export your data. Then use our{' '}
          <Link className="underline text-emerald-600" href="/free/categorizer">
            Free Categorizer
          </Link>{' '}
          to auto-categorize and download a clean CSV or export to QuickBooks.
        </p>

        <ol className="list-decimal pl-5 space-y-3 mb-8">
          {steps.map((step, i) => (
            <li key={i} className="text-gray-700">
              <strong>{step.title}:</strong> {step.body}
            </li>
          ))}
        </ol>

        <div className="flex gap-3 mb-12">
          <Link
            href="/free/categorizer"
            className="px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700 transition"
          >
            Use Free Categorizer
          </Link>
          <Link
            href="/pricing"
            className="px-4 py-2 rounded border border-gray-300 hover:bg-gray-50 transition"
          >
            See Pricing
          </Link>
        </div>

        {/* FAQ Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faq.map((item, i) => (
              <div key={i}>
                <h3 className="font-semibold text-gray-900 mb-1">{item.q}</h3>
                <p className="text-gray-600">{item.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Non-affiliation Disclaimer */}
        <p className="mt-10 text-xs text-gray-500 border-t pt-4">
          <strong>Disclaimer:</strong> This page is for informational purposes. {bank.name} is a
          trademark of its respective owner. AI Bookkeeper is not affiliated with or endorsed by{' '}
          {bank.name}.
        </p>
      </main>
    </>
  );
}
