import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { findBankByRouteSlug, getActiveBanks, toRouteSlug } from '@/lib/pse-banks';

export const dynamicParams = true;        // allow non-prebuilt slugs to render
export const revalidate = 86400;          // cache for a day

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
  const site = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app';
  if (!bank) {
    return { robots: { index: false, follow: true }, title: 'Guide not found' };
  }
  const title = `${bank.name} — Export Transactions to CSV (Guide)`;
  const canonical = `${site}/guides/${slug}`;
  const robots = bank.active ? { index: true, follow: true } : { index: false, follow: true };

  return {
    title,
    description: `Step-by-step: export ${bank.name} transactions to CSV and categorize with AI Bookkeeper.`,
    alternates: { canonical },
    robots,
    openGraph: {
      title,
      url: canonical,
      images: [`${site}/api/og/pse?slug=${slug}`],
      type: 'website'
    },
    twitter: { card: 'summary_large_image', title }
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const bank = findBankByRouteSlug(slug);
  if (!bank) return notFound();

  const howTo = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": `Export ${bank.name} transactions to CSV`,
    "step": [
      { "@type": "HowToStep", "name": "Log in", "text": `Sign in to ${bank.name} online banking.` },
      { "@type": "HowToStep", "name": "Go to activity", "text": "Open account or transactions." },
      { "@type": "HowToStep", "name": "Filter dates", "text": "Choose the desired date range." },
      { "@type": "HowToStep", "name": "Export CSV", "text": "Choose CSV and download the file." },
      { "@type": "HowToStep", "name": "Categorize", "text": "Upload to AI Bookkeeper to auto-categorize." }
    ]
  };

  const faq = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      { "@type": "Question", "name": `Where is ${bank.name}'s export?`,
        "acceptedAnswer": { "@type": "Answer", "text": "Usually in account activity or statements." } },
      { "@type": "Question", "name": "Which format is best?",
        "acceptedAnswer": { "@type": "Answer", "text": "CSV is best for import and cleanup." } },
      { "@type": "Question", "name": "Can I include categories?",
        "acceptedAnswer": { "@type": "Answer", "text": "Export raw, then categorize in AI Bookkeeper." } }
    ]
  };

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-bold mb-2">{bank.name} — Export Transactions to CSV</h1>
      <p className="text-gray-600 mb-6">
        Quick guide to download your {bank.name} transactions as CSV. Then use our
        {' '}<a className="underline" href="/free/categorizer">Free Categorizer</a>{' '}to clean and tag them.
      </p>

      <ol className="list-decimal pl-6 space-y-2">
        <li>Sign in to {bank.name} online banking.</li>
        <li>Open account activity.</li>
        <li>Choose your date range.</li>
        <li>Export as CSV.</li>
        <li>Upload to the Free Categorizer.</li>
      </ol>

      <div className="mt-8">
        <a href="/free/categorizer" className="inline-block rounded bg-emerald-600 px-4 py-2 text-white">
          Use Free Categorizer
        </a>
        <a href="/pricing" className="ml-3 underline">See pricing</a>
      </div>

      <p className="mt-8 text-xs text-gray-500">
        Not affiliated with {bank.name}. Names are for identification only.
      </p>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(howTo) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faq) }} />
    </main>
  );
}
