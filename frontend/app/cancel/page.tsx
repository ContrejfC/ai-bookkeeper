'use client';

import { Button, Card, CardBody } from '@nextui-org/react';

export default function CancelPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 py-16">
      <div className="container mx-auto px-4 max-w-3xl">
        <Card className="shadow-xl">
          <CardBody className="p-12 text-center space-y-6">
            <div className="text-6xl mb-4">😔</div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Checkout Cancelled
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              No worries! You can come back anytime when you're ready.
            </p>

            <div className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg my-8">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Still Interested?
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Check out our free CSV cleaner tool or learn more about our features
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
              <Button
                as="a"
                href="/pricing"
                color="primary"
                size="lg"
                className="min-w-[200px]"
              >
                View Pricing
              </Button>
              <Button
                as="a"
                href="/tools/csv-cleaner"
                color="default"
                variant="bordered"
                size="lg"
                className="min-w-[200px]"
              >
                Try Free Tool
              </Button>
            </div>

            <div className="pt-8 text-sm text-gray-600 dark:text-gray-400">
              <p>
                Have questions?{' '}
                <a href="mailto:support@ai-bookkeeper.app" className="text-blue-600 hover:underline">
                  Contact us
                </a>
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

