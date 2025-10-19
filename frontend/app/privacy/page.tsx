import { Card, CardBody } from '@nextui-org/react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-16">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Privacy Policy</h1>
        
        <Card>
          <CardBody className="prose dark:prose-invert max-w-none p-8">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
            </p>

            <h2>1. Information We Collect</h2>
            <p>
              We collect information you provide directly to us, including name, email address, company
              information, and financial data you upload for processing.
            </p>

            <h2>2. How We Use Your Information</h2>
            <p>We use the information we collect to:</p>
            <ul>
              <li>Provide, maintain, and improve our services</li>
              <li>Process transactions and send related information</li>
              <li>Send technical notices and support messages</li>
              <li>Respond to your comments and questions</li>
            </ul>

            <h2>3. Data Security</h2>
            <p>
              We implement appropriate technical and organizational measures to protect your personal
              information against unauthorized access, alteration, disclosure, or destruction. All data
              is encrypted in transit and at rest.
            </p>

            <h2>4. Data Retention</h2>
            <p>
              We retain your data for as long as your account is active or as needed to provide you
              services. Standard retention is 12 months, with optional extended retention available.
            </p>

            <h2>5. Your Rights</h2>
            <p>You have the right to:</p>
            <ul>
              <li>Access your personal information</li>
              <li>Correct inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Export your data</li>
              <li>Opt-out of marketing communications</li>
            </ul>

            <h2>6. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy, please contact us at{' '}
              <a href="mailto:privacy@ai-bookkeeper.app" className="text-blue-600">
                privacy@ai-bookkeeper.app
              </a>
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

