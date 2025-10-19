import { Card, CardBody } from '@nextui-org/react';

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-16">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Security</h1>
        
        <Card className="mb-8">
          <CardBody className="p-8">
            <p className="text-lg text-gray-700 dark:text-gray-300">
              Security is at the core of everything we do. We implement industry-leading practices
              to protect your financial data.
            </p>
          </CardBody>
        </Card>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <Card>
            <CardBody className="p-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                🔒 Encryption
              </h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• TLS 1.3 for data in transit</li>
                <li>• AES-256 for data at rest</li>
                <li>• End-to-end encryption for sensitive fields</li>
              </ul>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                🛡️ Compliance
              </h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• SOC 2 Type II certified</li>
                <li>• GDPR compliant</li>
                <li>• CCPA compliant</li>
              </ul>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                👤 Access Control
              </h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• Multi-factor authentication (MFA)</li>
                <li>• Role-based access control (RBAC)</li>
                <li>• SSO with SAML (Enterprise)</li>
              </ul>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-6">
              <h3 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">
                🔍 Monitoring
              </h3>
              <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                <li>• 24/7 security monitoring</li>
                <li>• Automated threat detection</li>
                <li>• Regular penetration testing</li>
              </ul>
            </CardBody>
          </Card>
        </div>

        <Card>
          <CardBody className="prose dark:prose-invert max-w-none p-8">
            <h2>Infrastructure Security</h2>
            <p>
              Our infrastructure is hosted on AWS with industry-leading security certifications.
              All servers are hardened, regularly patched, and monitored 24/7.
            </p>

            <h2>Data Isolation</h2>
            <p>
              Each customer's data is logically isolated using multi-tenant architecture with
              row-level security. Enterprise customers can opt for dedicated instances.
            </p>

            <h2>Backup and Recovery</h2>
            <p>
              All data is backed up daily with point-in-time recovery capability. Backups are
              encrypted and stored in geographically distributed locations.
            </p>

            <h2>Incident Response</h2>
            <p>
              We maintain a comprehensive incident response plan with clear escalation procedures.
              Customers are notified within 48 hours of any security incidents affecting their data.
            </p>

            <h2>Vulnerability Management</h2>
            <p>
              We conduct regular vulnerability scans and penetration tests. Critical vulnerabilities
              are patched within 24 hours, high-severity within 7 days.
            </p>

            <h2>Employee Training</h2>
            <p>
              All employees undergo security training and sign confidentiality agreements.
              Access to customer data is strictly limited and logged.
            </p>

            <h2>Report a Security Issue</h2>
            <p>
              If you discover a security vulnerability, please report it to{' '}
              <a href="mailto:security@ai-bookkeeper.app" className="text-blue-600">
                security@ai-bookkeeper.app
              </a>
              . We have a responsible disclosure policy and appreciate your help in keeping our
              platform secure.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

