/**
 * Screenshot Disclaimer Component
 * ================================
 * 
 * Legal disclaimer for programmatic SEO pages.
 * Shown at bottom of pages that include screenshots or UI illustrations.
 */

import { Link } from '@nextui-org/react';

export function ScreenshotDisclaimer() {
  return (
    <div className="mt-12 pt-8 border-t border-gray-200">
      <p className="text-xs text-gray-500 text-center max-w-3xl mx-auto">
        Screenshots and UI illustrations are for educational and demonstrative purposes only. 
        Product names, logos, and trademarks are property of their respective owners. 
        For removal requests or trademark concerns, contact{' '}
        <Link 
          href="mailto:privacy@ai-bookkeeper.app" 
          className="text-blue-600 hover:underline text-xs"
        >
          privacy@ai-bookkeeper.app
        </Link>
        .
      </p>
    </div>
  );
}

