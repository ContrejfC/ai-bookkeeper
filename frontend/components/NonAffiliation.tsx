/**
 * NonAffiliation Component
 * ========================
 * 
 * Trademark/brand safety disclaimer for programmatic SEO pages.
 * Ensures compliance with trademark nominative use guidelines.
 */

interface NonAffiliationProps {
  bankName?: string;
  className?: string;
}

export function NonAffiliation({ bankName, className = '' }: NonAffiliationProps) {
  const disclaimer = bankName
    ? `All product names, logos, and brands are property of their respective owners. AI Bookkeeper is not affiliated with, endorsed by, or sponsored by ${bankName}.`
    : 'All product names, logos, and brands are property of their respective owners. AI Bookkeeper is not affiliated with, endorsed by, or sponsored by any financial institution mentioned on this site.';

  return (
    <div 
      className={`border-t border-gray-200 dark:border-gray-700 pt-6 mt-12 ${className}`}
      role="contentinfo"
      aria-label="Disclaimer"
    >
      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
        <strong>Disclaimer:</strong> {disclaimer} This guide is provided for informational purposes only.
      </p>
    </div>
  );
}

