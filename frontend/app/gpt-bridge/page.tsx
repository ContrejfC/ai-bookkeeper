'use client';

import { useEffect } from 'react';
import { Button } from '@nextui-org/react';
import { trackBridgeViewed, trackOpenGptClicked } from '@/lib/analytics';

export default function GPTBridgePage() {
  const gptDeepLink = process.env.NEXT_PUBLIC_GPT_DEEPLINK || '#';

  useEffect(() => {
    trackBridgeViewed();
  }, []);

  const handleOpenGPT = () => {
    trackOpenGptClicked();
    window.open(gptDeepLink, '_blank');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <div className="text-center space-y-8">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white">
            Run AI Bookkeeper in ChatGPT
          </h1>

          <p className="text-xl text-gray-600 dark:text-gray-300">
            Use our powerful AI bookkeeping assistant directly inside ChatGPT with GPT Actions
          </p>

          <div className="py-8">
            <Button
              color="primary"
              size="lg"
              className="text-lg px-12 py-6"
              onClick={handleOpenGPT}
            >
              Open in ChatGPT
            </Button>
          </div>

          <div className="mt-16 p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
              No ChatGPT account?
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Try our web-based CSV cleaner tool—no account needed
            </p>
            <Button
              as="a"
              href="/tools/csv-cleaner"
              color="default"
              variant="bordered"
              size="lg"
            >
              Try CSV Cleaner
            </Button>
          </div>

          <div className="mt-16 grid md:grid-cols-3 gap-8 text-left">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                🤖 AI-Powered
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Automatically categorize transactions and suggest journal entries
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                ⚡ Lightning Fast
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Process hundreds of transactions in seconds
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                🔒 Secure
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Bank-level encryption and SOC 2 compliance
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

