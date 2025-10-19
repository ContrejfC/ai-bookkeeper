'use client';

import { useState } from 'react';
import { Button, Card, CardBody, CardHeader, Switch, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Input, Textarea } from '@nextui-org/react';
import { trackCheckoutClicked } from '@/lib/analytics';

interface Plan {
  id: string;
  name: string;
  price: number;
  annualPrice: number;
  entities: number;
  transactions: number;
  overageRate: number;
  features: string[];
  cta: string;
  popular?: boolean;
  description: string;
}

const plans: Plan[] = [
  {
    id: 'starter',
    name: 'Starter',
    price: 49,
    annualPrice: 41, // 17% discount
    entities: 1,
    transactions: 500,
    overageRate: 0.03,
    description: 'For solo SMBs',
    features: [
      'OCR with bounding boxes',
      'Propose/review/export',
      'QuickBooks & Xero integration',
      'Email support',
    ],
    cta: 'Start Starter',
  },
  {
    id: 'team',
    name: 'Team',
    price: 149,
    annualPrice: 124, // 17% discount
    entities: 3,
    transactions: 2000,
    overageRate: 0.02,
    description: 'For small firms or operations teams',
    features: [
      'Everything in Starter',
      'Rules versioning',
      'Bulk approve',
      'Email ingest',
      'Priority email support',
    ],
    cta: 'Start Team',
    popular: true,
  },
  {
    id: 'firm',
    name: 'Firm',
    price: 499,
    annualPrice: 414, // 17% discount
    entities: 10,
    transactions: 10000,
    overageRate: 0.015,
    description: 'For bookkeeping firms with multiple clients',
    features: [
      'Everything in Team',
      'API access',
      'Audit exports',
      'Role-based access control',
      'Quarterly review',
      '99.5% SLA',
      'Priority support (24h target)',
    ],
    cta: 'Start Firm',
  },
];

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);
  const [contactModalOpen, setContactModalOpen] = useState(false);
  const [pilotModalOpen, setPilotModalOpen] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    company: '',
    message: '',
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';

  const handleCheckout = async (planId: string) => {
    const term = annual ? 'annual' : 'monthly';
    trackCheckoutClicked(planId, term);

    try {
      const response = await fetch(`${apiUrl}/api/billing/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: planId,
          term,
          addons: [],
        }),
      });

      if (!response.ok) {
        throw new Error('Checkout failed');
      }

      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Failed to start checkout. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 py-16">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Choose the plan that fits your business
          </p>

          {/* Annual Toggle */}
          <div className="flex items-center justify-center gap-4">
            <span className={`text-lg ${!annual ? 'font-semibold' : ''}`}>Monthly</span>
            <Switch isSelected={annual} onValueChange={setAnnual} size="lg" />
            <span className={`text-lg ${annual ? 'font-semibold' : ''}`}>
              Annual <span className="text-green-600">(Save 17%)</span>
            </span>
          </div>
        </div>

        {/* Pilot Offer Banner */}
        <div className="mb-12 p-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg shadow-lg text-white text-center">
          <h3 className="text-2xl font-bold mb-2">Limited Pilot Offer</h3>
          <p className="text-lg mb-4">
            $99/month for 3 months • Up to 3 entities & 3,000 transactions
          </p>
          <p className="mb-4">Auto-migrates to Team or Firm after pilot • Cancel anytime</p>
          <Button
            color="default"
            variant="solid"
            size="lg"
            className="bg-white text-purple-600 font-semibold"
            onClick={() => setPilotModalOpen(true)}
          >
            Join Pilot Program
          </Button>
        </div>

        {/* Plans Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {plans.map((plan) => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? 'border-2 border-blue-500 shadow-xl scale-105'
                  : 'border border-gray-200 dark:border-gray-700'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </span>
                </div>
              )}
              <CardHeader className="flex-col items-start pt-8">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{plan.name}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{plan.description}</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">
                    ${annual ? plan.annualPrice : plan.price}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400">/month</span>
                  {annual && (
                    <div className="text-sm text-green-600 dark:text-green-400">
                      Save ${(plan.price - plan.annualPrice) * 12}/year
                    </div>
                  )}
                </div>
                <div className="mt-4 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <div>
                    <strong>{plan.entities}</strong> {plan.entities === 1 ? 'entity' : 'entities'}
                  </div>
                  <div>
                    <strong>{plan.transactions.toLocaleString()}</strong> transactions/month
                  </div>
                  <div>
                    Overage: <strong>${plan.overageRate}</strong> per transaction
                  </div>
                </div>
              </CardHeader>
              <CardBody className="pt-0">
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-500 mt-1">✓</span>
                      <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  color="primary"
                  variant={plan.popular ? 'solid' : 'bordered'}
                  size="lg"
                  className="w-full"
                  onClick={() => handleCheckout(plan.id)}
                >
                  {plan.cta}
                </Button>
              </CardBody>
            </Card>
          ))}
        </div>

        {/* Enterprise */}
        <Card className="mb-16 bg-gradient-to-r from-gray-900 to-gray-800 text-white">
          <CardBody className="p-8">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-3xl font-bold mb-4">Enterprise</h3>
                <p className="text-gray-300 mb-4">For compliance-heavy companies</p>
                <ul className="space-y-2 mb-6">
                  <li>• 25+ entities & 25,000+ transactions/month</li>
                  <li>• Overage: $0.01 per transaction</li>
                  <li>• SSO with SAML</li>
                  <li>• Data Processing Agreement (DPA)</li>
                  <li>• Custom retention policies</li>
                  <li>• 99.9% SLA</li>
                  <li>• Dedicated success manager</li>
                </ul>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-4">Custom Pricing</div>
                <Button
                  color="default"
                  variant="solid"
                  size="lg"
                  className="bg-white text-gray-900"
                  onClick={() => setContactModalOpen(true)}
                >
                  Contact Sales
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Add-ons */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">
            Optional Add-ons
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardBody>
                <h4 className="font-semibold text-lg mb-2">Extra Entity</h4>
                <p className="text-2xl font-bold text-blue-600 mb-2">$25/mo</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Starter & Team: $25/mo • Firm: $15/mo
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold text-lg mb-2">SSO (SAML)</h4>
                <p className="text-2xl font-bold text-blue-600 mb-2">$99/mo</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Single sign-on integration
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold text-lg mb-2">White-label</h4>
                <p className="text-2xl font-bold text-blue-600 mb-2">$149/mo</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Custom branding for your firm
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold text-lg mb-2">Extended Retention</h4>
                <p className="text-2xl font-bold text-blue-600 mb-2">$49/mo</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  24 months instead of 12 months
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold text-lg mb-2">Priority Support</h4>
                <p className="text-2xl font-bold text-blue-600 mb-2">$99/mo</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  24-hour response time (included in Firm+)
                </p>
              </CardBody>
            </Card>
          </div>
        </div>

        {/* FAQ / Billing Rules */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">
            Billing & Usage
          </h2>
          <div className="space-y-6">
            <Card>
              <CardBody>
                <h4 className="font-semibold mb-2">What counts as a billable transaction?</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  A billable transaction is a bank or card line that is ingested and processed through
                  our propose endpoint. Idempotent retries and re-exports are not billed.
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold mb-2">When does my quota reset?</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  Your monthly transaction quota resets on the first day of each calendar month. Overage
                  charges are calculated and billed at month end.
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <h4 className="font-semibold mb-2">Do you offer discounts?</h4>
                <p className="text-gray-600 dark:text-gray-400">
                  Yes! Annual prepay receives a 17% discount. Nonprofit organizations receive an
                  additional 10% discount on all plans.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>

      {/* Contact Modal */}
      <Modal isOpen={contactModalOpen} onClose={() => setContactModalOpen(false)} size="2xl">
        <ModalContent>
          <ModalHeader>Contact Enterprise Sales</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <Input
                label="Name"
                placeholder="Your name"
                value={contactForm.name}
                onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
              />
              <Input
                label="Email"
                type="email"
                placeholder="your@email.com"
                value={contactForm.email}
                onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
              />
              <Input
                label="Company"
                placeholder="Your company"
                value={contactForm.company}
                onChange={(e) => setContactForm({ ...contactForm, company: e.target.value })}
              />
              <Textarea
                label="Message"
                placeholder="Tell us about your needs..."
                value={contactForm.message}
                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
              />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onClick={() => setContactModalOpen(false)}>
              Cancel
            </Button>
            <Button color="primary" onClick={() => alert('Contact form submitted!')}>
              Send Message
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Pilot Modal */}
      <Modal isOpen={pilotModalOpen} onClose={() => setPilotModalOpen(false)}>
        <ModalContent>
          <ModalHeader>Join Pilot Program</ModalHeader>
          <ModalBody>
            <p className="mb-4">
              Our pilot program gives you access to full Team features at just $99/month for 3 months.
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
              <li>Up to 3 entities</li>
              <li>3,000 transactions per month</li>
              <li>All Team features included</li>
              <li>Auto-migrates to Team or Firm after 3 months</li>
              <li>Cancel anytime, no commitment</li>
            </ul>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onClick={() => setPilotModalOpen(false)}>
              Cancel
            </Button>
            <Button color="primary" onClick={() => handleCheckout('pilot')}>
              Start Pilot
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}

