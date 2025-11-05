'use client';

/**
 * PSE Analytics Tracker
 * =====================
 * 
 * Client component for tracking PSE guide page views and CTA clicks.
 */

import { useEffect } from 'react';
import { trackPSEPageView, trackPSECtaClicked } from '@/lib/analytics';

interface PSEAnalyticsProps {
  slug: string;
  bankName: string;
  format?: string;
}

export function PSEAnalytics({ slug, bankName, format = 'csv' }: PSEAnalyticsProps) {
  useEffect(() => {
    // Track page view on mount
    trackPSEPageView(slug, bankName, format);
  }, [slug, bankName, format]);

  return null; // This component doesn't render anything
}

/**
 * Trackable Link Component
 * 
 * Wraps a link to track CTA clicks
 */
interface PSECtaLinkProps {
  href: string;
  slug: string;
  cta: 'free_categorizer' | 'pricing';
  children: React.ReactNode;
  className?: string;
}

export function PSECtaLink({ href, slug, cta, children, className }: PSECtaLinkProps) {
  const handleClick = () => {
    trackPSECtaClicked(cta, slug);
  };

  return (
    <a href={href} className={className} onClick={handleClick}>
      {children}
    </a>
  );
}

