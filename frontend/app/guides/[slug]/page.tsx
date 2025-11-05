/**
 * Bank Export Guide Page
 * =======================
 * SSG for active banks, on-demand for noindex.
 */

import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import { getActiveBanks, findBankByRouteSlug, toRouteSlug } from '@/lib/pse-banks';

export const dynamic = 'error'; // Force SSG
export const revalidate = 86400;

const SITE = 'https://ai-bookkeeper.app';

// Pre-build active banks only
export async function generateStaticParams() {
  return getActiveBanks().map(b => ({ slug: toRouteSlug(b.slug) }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const bank = findBankByRouteSlug(slug);
  if (!bank) return { robots: { index: false, follow: true } };

  const url = `${SITE}/guides/${slug}`;
  const title = `${bank.name} — Export Transactions to CSV (Guide)`;
  const desc = `Step-by-step: export ${bank.name} transactions to CSV. Then auto-categorize with the Free Categorizer.`;

  return {
    title,
    description: desc,
    alternates: { canonical: url },
    robots: bank.active ? { index: true, follow: true } : { index: false, follow: true },
    openGraph: {
      title,
      description: desc,
      url,
      images: [`${SITE}/api/og/pse?slug=${encodeURIComponent(slug)}`],
      type: 'article',
    },
    twitter: { card: 'summary_large_image', title, description: desc },
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const bank = findBankByRouteSlug(slug);
  if (!bank) return notFound();

  // JSON-LD: HowTo
  const howTo = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: `How to export ${bank.name} transactions to CSV`,
    step: [
      { '@type': 'HowToStep', position: 1, name: `Sign in to ${bank.name}`, text: `Visit your ${bank.name} online banking portal.` },
      { '@type': 'HowToStep', position: 2, name: 'Go to Transactions', text: 'Navigate to the Transactions or Activity section.' },
      { '@type': 'HowToStep', position: 3, name: 'Select date range', text: 'Choose the date range for transactions to export.' },
      { '@type': 'HowToStep', position: 4, name: 'Download CSV', text: 'Click Export or Download and select CSV format.' },
      { '@type': 'HowToStep', position: 5, name: 'Categorize', text: 'Upload to the Free Categorizer for instant organization.' },
    ],
  };

  // JSON-LD: FAQ
  const faq = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: `How do I export ${bank.name} transactions to CSV?`,
        acceptedAnswer: {
          '@type': 'Answer',
          text: `Log in to ${bank.name} online banking, go to Transactions, select your date range, then download in CSV format.`,
        },
      },
      {
        '@type': 'Question',
        name: `Can I export business transactions from ${bank.name}?`,
        acceptedAnswer: {
          '@type': 'Answer',
          text: `Yes, most ${bank.name} business accounts support CSV exports through the business banking portal.`,
        },
      },
    ],
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howTo) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faq) }} />
      
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-bold mb-2">{bank.name}: Export Transactions to CSV</h1>
        <p className="text-gray-600 mb-6">
          Follow these steps to export your data. Then use our{' '}
          <Link className="underline text-emerald-600" href="/free/categorizer">
            Free Categorizer
          </Link>{' '}
          to auto-categorize and download a clean CSV or export to QuickBooks.
        </p>

        <ol className="list-decimal pl-5 space-y-2 mb-8">
          <li>Sign in to your {bank.name} online banking.</li>
          <li>Go to Transactions or Activity.</li>
          <li>Select date range and click Export.</li>
          <li>Choose CSV. Download the file.</li>
          <li>Open the CSV in the Free Categorizer and verify categories.</li>
        </ol>

        <div className="flex gap-3 mb-12">
          <Link
            href="/free/categorizer"
            className="px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700"
          >
            Use Free Categorizer
          </Link>
          <Link href="/pricing" className="px-4 py-2 rounded border hover:bg-gray-50">
            See Pricing
          </Link>
        </div>

        <p className="mt-10 text-xs text-gray-500 border-t pt-4">
          This page is for informational purposes. {bank.name} is a trademark of its respective owner.
          AI Bookkeeper is not affiliated with or endorsed by {bank.name}.
        </p>
      </main>
    </>
  );
}
