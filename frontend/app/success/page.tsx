'use client';

import { useEffect, Suspense } from 'react';
import { Button, Card, CardBody } from '@nextui-org/react';
import { trackPurchase, trackSubscriptionStarted } from '@/lib/analytics';
import { useSearchParams } from 'next/navigation';

function SuccessContent() {
  const searchParams = useSearchParams();
  
  useEffect(() => {
    // Extract plan and amount from query params if available
    const plan = searchParams.get('plan') || 'unknown';
    const amount = parseFloat(searchParams.get('amount') || '0');
    
    if (amount > 0) {
      trackPurchase(amount, 'USD', plan);
      trackSubscriptionStarted(amount, 'USD', plan);
    }
  }, [searchParams]);

  const gptDeepLink = process.env.NEXT_PUBLIC_GPT_DEEPLINK || '/gpt-bridge';

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-gray-800 py-16">
      <div className="container mx-auto px-4 max-w-3xl">
        <Card className="shadow-xl">
          <CardBody className="p-12 text-center space-y-6">
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Welcome to AI Bookkeeper!
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Your subscription is now active. Let's get started!
            </p>

            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg my-8">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Next Steps
              </h2>
              <ol className="text-left space-y-3 text-gray-700 dark:text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="font-bold">1.</span>
                  <span>Reconnect in ChatGPT using our GPT Actions integration</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">2.</span>
                  <span>Or use the CSV Cleaner tool to start processing transactions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">3.</span>
                  <span>Connect your QuickBooks or Xero account</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">4.</span>
                  <span>Upload your first bank statement and watch the magic happen!</span>
                </li>
              </ol>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
              <Button
                as="a"
                href={gptDeepLink}
                color="primary"
                size="lg"
                className="min-w-[200px]"
              >
                Open in ChatGPT
              </Button>
              <Button
                as="a"
                href="/tools/csv-cleaner"
                color="default"
                variant="bordered"
                size="lg"
                className="min-w-[200px]"
              >
                Try CSV Cleaner
              </Button>
            </div>

            <div className="pt-8 text-sm text-gray-600 dark:text-gray-400">
              <p>
                Need help getting started?{' '}
                <a href="mailto:support@ai-bookkeeper.app" className="text-blue-600 hover:underline">
                  Contact our support team
                </a>
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-gray-800 py-16 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}

