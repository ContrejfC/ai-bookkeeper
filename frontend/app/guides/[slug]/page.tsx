/**
 * Bank Export Guide - Dynamic Page
 * ==================================
 * 
 * Programmatic SEO pages for bank transaction export guides.
 * Each page targets queries like "<bank> export CSV", "<bank> transactions to QuickBooks".
 */

import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  getBankBySlug,
  getAllBankSlugs,
  getDefaultExportSteps,
  getDefaultFAQ,
  type BankRecord,
} from '@/lib/pse-banks';
import { NonAffiliation } from '@/components/NonAffiliation';
import { PSEAnalytics } from '@/components/PSEAnalytics';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app';

// Generate static params for all bank slugs
export async function generateStaticParams() {
  const slugs = getAllBankSlugs();
  return slugs.map((slug) => ({
    slug,
  }));
}

// Generate metadata for each page
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const bank = getBankBySlug(slug);

  if (!bank) {
    return {
      title: 'Guide Not Found',
      description: 'Bank export guide not found.',
    };
  }

  const title = `${bank.bankName} — Export Transactions to CSV (Guide)`;
  const description = `Learn to export ${bank.bankName} transactions to CSV and categorize them in minutes. Step-by-step instructions plus a free CSV categorizer.`;
  const canonical = `${SITE_URL}/guides/${slug}`;

  return {
    title,
    description,
    alternates: {
      canonical,
    },
    robots: {
      index: bank.status === 'active',
      follow: true,
    },
    openGraph: {
      title,
      description,
      url: canonical,
      siteName: 'AI Bookkeeper',
      locale: 'en_US',
      type: 'article',
      images: [
        {
          url: `${SITE_URL}/api/og/pse?slug=${encodeURIComponent(slug)}`,
          width: 1200,
          height: 630,
          alt: `${bank.bankName} Export Guide`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [`${SITE_URL}/api/og/pse?slug=${encodeURIComponent(slug)}`],
    },
  };
}

// Page component
export default async function BankGuidePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const bank = getBankBySlug(slug);

  if (!bank) {
    notFound();
  }

  const steps = bank.steps.length > 0 ? bank.steps : getDefaultExportSteps(bank.bankName);
  const faq = bank.faq.length > 0 ? bank.faq : getDefaultFAQ(bank.bankName);

  // JSON-LD: HowTo Schema
  const howToSchema = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: `How to export ${bank.bankName} transactions to CSV`,
    description: `Step-by-step guide to export ${bank.bankName} bank transactions to CSV format for categorization and accounting.`,
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
    mainEntity: faq.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  };

  // JSON-LD: BreadcrumbList Schema
  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: SITE_URL,
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Guides',
        item: `${SITE_URL}/guides`,
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: `${bank.bankName} Export Guide`,
        item: `${SITE_URL}/guides/${slug}`,
      },
    ],
  };

  return (
    <>
      {/* Analytics Tracker */}
      <PSEAnalytics slug={slug} bankName={bank.bankName} format={bank.primaryFormat} />

      {/* JSON-LD Schemas */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      {/* Page Content */}
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 py-16">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <header className="mb-12">
            {/* Breadcrumb */}
            <nav className="mb-4" aria-label="Breadcrumb">
              <ol className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <li>
                  <Link href="/" className="hover:text-emerald-600 dark:hover:text-emerald-400">
                    Home
                  </Link>
                </li>
                <li>&rsaquo;</li>
                <li>
                  <Link href="/guides" className="hover:text-emerald-600 dark:hover:text-emerald-400">
                    Guides
                  </Link>
                </li>
                <li>&rsaquo;</li>
                <li className="text-gray-900 dark:text-white font-medium" aria-current="page">
                  {bank.bankName}
                </li>
              </ol>
            </nav>

            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              How to export {bank.bankName} transactions to CSV
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Step-by-step export + free CSV categorizer.
            </p>

            {/* Trust Strip */}
            <div className="flex flex-wrap items-center gap-4 mt-6 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Free tool</span>
              </div>
              <span className="text-gray-400">•</span>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>No signup required</span>
              </div>
              <span className="text-gray-400">•</span>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Instant results</span>
              </div>
            </div>

            {/* Primary CTAs */}
            <div className="flex flex-wrap gap-4 mt-8">
              <Link
                href="/free/categorizer"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors"
              >
                Use Free Categorizer
                <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-base font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors"
              >
                See pricing
              </Link>
            </div>
          </header>

          {/* How It Works Steps */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              How it works
            </h2>
            <ol className="space-y-6">
              {steps.map((step, index) => (
                <li key={index} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-emerald-600 text-white font-bold text-lg">
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1 pt-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {step.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300">
                      {step.body}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          {/* Supported Formats */}
          <section className="mb-12 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
              Supported formats
            </h2>
            <p className="text-gray-700 dark:text-gray-300 mb-3">
              {bank.bankName} typically supports the following export formats:
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
              {bank.formats.map((format) => (
                <li key={format}>
                  <strong>{format.toUpperCase()}</strong> — {
                    format === 'csv' ? 'Comma-separated values (universal, recommended)' :
                    format === 'ofx' ? 'Open Financial Exchange (for Quicken, QuickBooks)' :
                    format === 'qfx' ? 'Quicken Financial Exchange (for Quicken)' :
                    'Compatible with most accounting software'
                  }
                </li>
              ))}
            </ul>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
              We recommend <strong>CSV</strong> for the best compatibility with our categorizer tool.
            </p>
          </section>

          {/* Troubleshooting / Quirks */}
          {bank.notes.quirks && bank.notes.quirks.length > 0 && (
            <section className="mb-12 p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-100 dark:border-yellow-800">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                Tips & troubleshooting
              </h2>
              <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                {bank.notes.quirks.map((quirk, index) => (
                  <li key={index}>{quirk}</li>
                ))}
              </ul>
            </section>
          )}

          {/* FAQ Section */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Frequently asked questions
            </h2>
            <div className="space-y-6">
              {faq.map((item, index) => (
                <div key={index}>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {item.q}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300">
                    {item.a}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Next Steps CTA */}
          <section className="mb-12 p-8 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-lg text-white">
            <h2 className="text-2xl font-bold mb-3">
              Ready to categorize your {bank.bankName} transactions?
            </h2>
            <p className="text-lg mb-6 opacity-90">
              Upload your CSV file and get instant AI-powered categorization. No signup required.
            </p>
            <Link
              href="/free/categorizer"
              className="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-base font-medium rounded-md text-white hover:bg-white hover:text-emerald-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white transition-colors"
            >
              Try Free Categorizer Now
              <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </section>

          {/* Related Links */}
          <section className="mb-12">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Related resources
            </h2>
            <ul className="space-y-2 text-gray-700 dark:text-gray-300">
              <li>
                <Link href="/free/categorizer" className="text-emerald-600 dark:text-emerald-400 hover:underline">
                  → Free CSV Categorizer
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-emerald-600 dark:text-emerald-400 hover:underline">
                  → Pricing & Plans
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-emerald-600 dark:text-emerald-400 hover:underline">
                  → Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/security" className="text-emerald-600 dark:text-emerald-400 hover:underline">
                  → Security & Compliance
                </Link>
              </li>
            </ul>
          </section>

          {/* Non-Affiliation Disclaimer */}
          <NonAffiliation bankName={bank.bankName} />
        </div>
      </div>
    </>
  );
}

