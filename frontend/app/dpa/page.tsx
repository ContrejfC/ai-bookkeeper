import { Card, CardBody } from '@nextui-org/react';

export default function DPAPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-16">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
          Data Processing Agreement
        </h1>
        
        <Card>
          <CardBody className="prose dark:prose-invert max-w-none p-8">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
            </p>

            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              Available for Enterprise customers
            </p>

            <h2>1. Definitions</h2>
            <ul>
              <li><strong>Controller:</strong> The customer subscribing to AI Bookkeeper services</li>
              <li><strong>Processor:</strong> AI Bookkeeper Inc.</li>
              <li><strong>Personal Data:</strong> Data uploaded and processed by the service</li>
            </ul>

            <h2>2. Scope of Processing</h2>
            <p>
              The Processor shall process Personal Data only on documented instructions from the
              Controller, including with regard to transfers of personal data to third countries
              or international organizations.
            </p>

            <h2>3. Security Measures</h2>
            <p>The Processor implements:</p>
            <ul>
              <li>Encryption of data in transit (TLS 1.3+)</li>
              <li>Encryption of data at rest (AES-256)</li>
              <li>Regular security audits and penetration testing</li>
              <li>Access controls and authentication (MFA required)</li>
              <li>SOC 2 Type II compliance</li>
            </ul>

            <h2>4. Sub-processors</h2>
            <p>Current sub-processors include:</p>
            <ul>
              <li>Amazon Web Services (infrastructure)</li>
              <li>Stripe (payment processing)</li>
              <li>OpenAI (AI processing)</li>
            </ul>

            <h2>5. Data Subject Rights</h2>
            <p>
              The Processor shall assist the Controller in responding to requests from data subjects
              exercising their rights under GDPR/CCPA.
            </p>

            <h2>6. Data Breach Notification</h2>
            <p>
              The Processor shall notify the Controller without undue delay (within 48 hours) after
              becoming aware of a personal data breach.
            </p>

            <h2>7. Audits and Inspections</h2>
            <p>
              Enterprise customers have the right to conduct audits of the Processor's data processing
              activities upon reasonable notice.
            </p>

            <h2>8. Data Deletion</h2>
            <p>
              Upon termination of services, the Processor shall delete or return all personal data
              within 30 days, unless legal retention is required.
            </p>

            <h2>9. Contact for DPA</h2>
            <p>
              To execute a DPA for your Enterprise account, contact{' '}
              <a href="mailto:dpa@ai-bookkeeper.app" className="text-blue-600">
                dpa@ai-bookkeeper.app
              </a>
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

