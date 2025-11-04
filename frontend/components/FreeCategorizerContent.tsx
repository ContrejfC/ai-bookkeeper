/**
 * Free Categorizer - Rich Content Section
 * =======================================
 * 
 * SEO-optimized content section with FAQs, how-it-works, and internal links.
 * Server component for optimal SEO.
 */

import Link from 'next/link';
import { Card, CardBody } from '@nextui-org/react';

export function FreeCategorizerContent() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16 space-y-12">
      {/* How It Works */}
      <section>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          How it works
        </h2>
        <Card className="bg-gray-50 dark:bg-gray-800/50">
          <CardBody className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <p className="text-gray-700 dark:text-gray-300">
                  <strong>Upload</strong> a CSV, OFX, or QFX from your bank.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <p className="text-gray-700 dark:text-gray-300">
                  <strong>We normalize and auto-categorize transactions</strong> using AI trained on accounting best practices.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <p className="text-gray-700 dark:text-gray-300">
                  <strong>You verify categories</strong> and provide feedback to improve accuracy.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold">
                4
              </div>
              <div>
                <p className="text-gray-700 dark:text-gray-300">
                  <strong>Download a clean CSV or export to QuickBooks</strong> for seamless import.
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      </section>

      {/* Supported Formats */}
      <section>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Supported formats
        </h2>
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-lg text-gray-700 dark:text-gray-300">
            Our <strong>free bank statement categorizer</strong> supports CSV, OFX, and QFX files from any bank. 
            Whether you need to <strong>categorize bank transactions CSV</strong> files or convert <strong>OFX to CSV categories</strong>, 
            our <strong>automatic transaction categorizer</strong> handles common formats seamlessly.
          </p>
          <p className="text-gray-700 dark:text-gray-300 mt-4">
            PDF and image statements are supported on a best-effort basis. For best results, export directly from your 
            bank&apos;s online portal as CSV, OFX, or QFX.
          </p>
        </div>
      </section>

      {/* Why This Tool */}
      <section>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Why this tool
        </h2>
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-lg text-gray-700 dark:text-gray-300">
            Faster bookkeeping, cleaner imports, less manual tagging. Our <strong>QuickBooks import CSV mapping</strong> tool 
            ensures your transactions are properly categorized before import, saving hours of manual work.
          </p>
          <p className="text-gray-700 dark:text-gray-300 mt-4">
            Built with <Link href="/security" className="text-emerald-600 dark:text-emerald-400 hover:underline">SOC 2-aligned controls</Link>, 
            your data is processed securely and deleted within 24 hours. See our <Link href="/privacy" className="text-emerald-600 dark:text-emerald-400 hover:underline">privacy policy</Link> and{' '}
            <Link href="/dpa" className="text-emerald-600 dark:text-emerald-400 hover:underline">data processing agreement</Link> for details.
          </p>
        </div>
      </section>

      {/* FAQs */}
      <section id="faqs">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          Frequently Asked Questions
        </h2>
        <div className="space-y-6">
          {/* FAQ 1 */}
          <Card>
            <CardBody>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Is this safe?
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                Files are deleted within 24 hours by default. We only use your data for model improvement if you opt in at upload.
              </p>
            </CardBody>
          </Card>

          {/* FAQ 2 */}
          <Card>
            <CardBody>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Which banks are supported?
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                Any bank that can export CSV, OFX, or QFX. We also parse common OFX/QFX variations.
              </p>
            </CardBody>
          </Card>

          {/* FAQ 3 */}
          <Card>
            <CardBody>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Do you support QuickBooks?
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                Yes. Download a clean CSV for import or export directly to QuickBooks when signed in. 
                Upgrade to a <Link href="/pricing" className="text-emerald-600 dark:text-emerald-400 hover:underline">paid plan</Link> for 
                direct QuickBooks Online integration.
              </p>
            </CardBody>
          </Card>

          {/* FAQ 4 */}
          <Card>
            <CardBody>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                How many rows can I upload?
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                The free limit is 500 rows per file. Need more? Check our <Link href="/pricing" className="text-emerald-600 dark:text-emerald-400 hover:underline">pricing plans</Link> for 
                higher limits and advanced features.
              </p>
            </CardBody>
          </Card>

          {/* FAQ 5 */}
          <Card>
            <CardBody>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Do you keep my data?
              </h3>
              <p className="text-gray-700 dark:text-gray-300">
                No by default. Free uploads are wiped within 24 hours. Opt-in training is optional and off by default. 
                Read more in our <Link href="/privacy" className="text-emerald-600 dark:text-emerald-400 hover:underline">privacy policy</Link>.
              </p>
            </CardBody>
          </Card>
        </div>
      </section>

      {/* How to Export Clean CSV */}
      <section id="how-to-export">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          How to export a clean bank CSV
        </h2>
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-gray-700 dark:text-gray-300">
            For best results when using our categorize bank transactions CSV tool:
          </p>
          <ol className="text-gray-700 dark:text-gray-300 space-y-2 mt-4">
            <li>Log into your bank&apos;s online portal</li>
            <li>Navigate to the account you want to export</li>
            <li>Look for &quot;Export&quot;, &quot;Download&quot;, or &quot;Statements&quot;</li>
            <li>Choose CSV, OFX, or QFX format (avoid PDF when possible)</li>
            <li>Select your date range (up to 500 transactions for free)</li>
            <li>Download and upload the file above</li>
          </ol>
          <p className="text-gray-700 dark:text-gray-300 mt-4">
            Most banks support OFX (Open Financial Exchange) or QFX (Quicken Financial Exchange) which provide 
            richer transaction data for better automatic categorization.
          </p>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="bg-gradient-to-r from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 rounded-2xl p-8 text-center">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Need more power?
        </h3>
        <p className="text-gray-700 dark:text-gray-300 mb-6">
          Upgrade for unlimited transactions, QuickBooks/Xero direct integration, custom categorization rules, and dedicated support.
        </p>
        <Link 
          href="/pricing"
          className="inline-block bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-8 py-3 rounded-lg font-semibold hover:from-emerald-600 hover:to-cyan-600 transition-all"
        >
          View Pricing Plans
        </Link>
      </section>
    </div>
  );
}

