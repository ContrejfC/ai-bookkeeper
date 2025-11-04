/**
 * Free Categorizer Layout - SEO Metadata & Structured Data
 * =========================================================
 */

import { Metadata } from 'next';
import { metadata as categorizerMetadata } from './metadata';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper-nine.vercel.app';

export const metadata: Metadata = categorizerMetadata;

// JSON-LD Structured Data
const jsonLdSoftwareApplication = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AI Bookkeeper – Free Bank Transaction Categorizer",
  "applicationCategory": "FinanceApplication",
  "operatingSystem": "Web",
  "url": `${SITE_URL}/free/categorizer`,
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "author": {
    "@type": "Organization",
    "name": "AI Bookkeeper"
  },
  "privacyPolicy": `${SITE_URL}/privacy`
};

const jsonLdFAQ = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is this safe?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Files are deleted within 24 hours by default. We only use your data for model improvement if you opt in at upload."
      }
    },
    {
      "@type": "Question",
      "name": "Which banks are supported?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Any bank that can export CSV, OFX, or QFX. We also parse common OFX/QFX variations."
      }
    },
    {
      "@type": "Question",
      "name": "Do you support QuickBooks?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Download a clean CSV for import or export directly to QuickBooks when signed in."
      }
    },
    {
      "@type": "Question",
      "name": "How many rows can I upload?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The free limit is 500 rows per file."
      }
    },
    {
      "@type": "Question",
      "name": "Do you keep my data?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No by default. Free uploads are wiped within 24 hours. Opt-in training is optional and off by default."
      }
    }
  ]
};

const jsonLdBreadcrumb = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": SITE_URL
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Free Tools",
      "item": `${SITE_URL}/free`
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Free Categorizer",
      "item": `${SITE_URL}/free/categorizer`
    }
  ]
};

export default function FreeCategorizerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLdSoftwareApplication),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLdFAQ),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLdBreadcrumb),
        }}
      />
      {children}
    </>
  );
}

