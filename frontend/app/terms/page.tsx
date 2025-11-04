'use client';

import { Card, CardBody } from '@nextui-org/react';
import { formatPolicyDate } from '@/lib/config';

export default function TermsPage() {
  // Use November 3, 2025 as the last updated date
  const lastUpdated = formatPolicyDate(new Date('2025-11-03'));
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-16">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Terms of Service</h1>
        
        <Card>
          <CardBody className="prose dark:prose-invert max-w-none p-8">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              <strong>Last Updated:</strong> {lastUpdated}
            </p>

            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing or using AI Bookkeeper, you agree to be bound by these Terms of Service
              and all applicable laws and regulations.
            </p>

            <h2>2. Service Description</h2>
            <p>
              AI Bookkeeper provides automated bookkeeping services including transaction categorization,
              journal entry generation, and integration with accounting platforms.
            </p>

            <h2>3. User Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials and
              for all activities that occur under your account.
            </p>

            <h2>4. Subscription and Billing</h2>
            <ul>
              <li>Subscriptions are billed monthly or annually in advance</li>
              <li>A billable transaction is a bank/card line processed through our propose endpoint</li>
              <li>Monthly quotas reset on the first day of each calendar month</li>
              <li>Overage charges are billed at month end</li>
              <li>Idempotent retries and re-exports are not billed</li>
            </ul>

            <h2>5. Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul>
              <li>Use the service for any illegal purpose</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Interfere with or disrupt the service</li>
              <li>Upload malicious code or malware</li>
            </ul>

            <h2>6. Service Level Agreement</h2>
            <ul>
              <li>Starter & Team: Best effort availability</li>
              <li>Firm: 99.5% uptime SLA</li>
              <li>Enterprise: 99.9% uptime SLA</li>
            </ul>

            <h2>7. Limitation of Liability</h2>
            <p>
              AI Bookkeeper shall not be liable for any indirect, incidental, special, consequential,
              or punitive damages resulting from your use of the service.
            </p>

            <h2>8. Termination</h2>
            <p>
              You may cancel your subscription at any time. We may terminate or suspend access to
              our service immediately for violation of these Terms.
            </p>

            <h2>9. Contact</h2>
            <p>
              For questions about these Terms, contact us at{' '}
              <a href="mailto:legal@ai-bookkeeper.app" className="text-blue-600">
                legal@ai-bookkeeper.app
              </a>
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

