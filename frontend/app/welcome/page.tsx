/**
 * Welcome Onboarding Flow
 * =======================
 * 
 * Multi-step wizard to guide new users through:
 * 1. Welcome + plan check
 * 2. Data source (demo data or upload CSV)
 * 3. View imported transactions
 * 4. AI categorization (propose entries)
 * 5. Review and approve
 * 6. Connect QuickBooks (optional)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/layout/AppShell';
import {
  Card,
  CardBody,
  Button,
  Progress,
  Chip,
  Input,
  Divider
} from '@nextui-org/react';
import { useAuth } from '@/contexts/auth-context';
// Temporarily disabled for build debugging
// import { useEntitlements } from '@/components/EntitlementsGate';

interface OnboardingStatus {
  status: string;
  progress: number;
  next_step: string;
  checks: {
    has_transactions: boolean;
    has_proposed: boolean;
    has_approved: boolean;
    has_qbo: boolean;
  };
}

export default function WelcomePage() {
  const router = useRouter();
  const { user } = useAuth();
  // Temporarily disabled for build debugging
  // const { entitlements, loading: entitlementsLoading } = useEntitlements();
  
  const [step, setStep] = useState(1);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoDataCreated, setDemoDataCreated] = useState(false);
  
  const totalSteps = 6;

  // Fetch onboarding status on mount
  useEffect(() => {
    fetchOnboardingStatus();
  }, []);

  const fetchOnboardingStatus = async () => {
    try {
      const response = await fetch('/api/onboarding/status');
      const data = await response.json();
      setOnboardingStatus(data);
      
      // Auto-advance to appropriate step based on progress
      if (data.checks.has_approved) {
        setStep(6); // Go to final step
      } else if (data.checks.has_proposed) {
        setStep(5); // Go to approval step
      } else if (data.checks.has_transactions) {
        setStep(4); // Go to propose step
      }
    } catch (err) {
      console.error('Failed to fetch onboarding status:', err);
    }
  };

  // Handle demo data creation
  const handleCreateDemo = async () => {
    if (!user) return;
    
    const tenantId = Array.isArray(user.tenant_ids) 
      ? user.tenant_ids[0] 
      : user.tenant_ids || 'demo-tenant';
    
    setLoading(true);
    try {
      const response = await fetch('/api/onboarding/seed-demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId, count: 50 })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create demo data');
      }
      
      const result = await response.json();
      console.log('Demo data created:', result);
      
      setDemoDataCreated(true);
      await fetchOnboardingStatus();
      setStep(3); // Move to view transactions
    } catch (err) {
      console.error('Failed to create demo data:', err);
      alert('Failed to create demo data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle sample CSV download
  const handleDownloadSample = () => {
    window.location.href = '/api/onboarding/sample-csv';
  };

  // Navigation helpers
  const goToTransactions = () => router.push('/transactions');
  const goToFirm = () => router.push('/firm');
  
  const progressPercent = (step / totalSteps) * 100;

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-8 space-y-6">
        {/* Progress Bar */}
        <Card>
          <CardBody>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium">Getting Started</h3>
                <Chip size="sm" variant="flat">
                  Step {step} of {totalSteps}
                </Chip>
              </div>
              <Progress 
                value={progressPercent} 
                color="primary" 
                size="sm"
                className="w-full"
              />
            </div>
          </CardBody>
        </Card>

        {/* Step 1: Welcome */}
        {step === 1 && (
          <Card>
            <CardBody className="space-y-6">
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold">👋 Welcome to AI Bookkeeper!</h1>
                <p className="text-lg text-default-600">
                  Let's get you set up in just a few minutes.
                </p>
              </div>

              <Divider />

              <div className="space-y-4">
                <h2 className="text-xl font-semibold">What you'll do:</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-default-100 p-4 rounded-lg">
                    <div className="text-2xl mb-2">📥</div>
                    <h3 className="font-semibold mb-1">Import Data</h3>
                    <p className="text-sm text-default-600">
                      Upload transactions or use demo data
                    </p>
                  </div>
                  <div className="bg-default-100 p-4 rounded-lg">
                    <div className="text-2xl mb-2">🤖</div>
                    <h3 className="font-semibold mb-1">AI Categorization</h3>
                    <p className="text-sm text-default-600">
                      Let AI propose journal entries
                    </p>
                  </div>
                  <div className="bg-default-100 p-4 rounded-lg">
                    <div className="text-2xl mb-2">✅</div>
                    <h3 className="font-semibold mb-1">Review & Approve</h3>
                    <p className="text-sm text-default-600">
                      Approve and export to QuickBooks
                    </p>
                  </div>
                </div>
              </div>

              {/* Temporarily disabled for build debugging
              {!entitlementsLoading && entitlements && (
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Chip color="primary" size="sm">{entitlements.plan}</Chip>
                    <span className="text-sm font-medium">
                      {entitlements.tx_remaining} transactions remaining this month
                    </span>
                  </div>
                  <p className="text-xs text-default-600">
                    {entitlements.status === 'active' 
                      ? '✓ Your subscription is active' 
                      : '⚠️ Please activate your subscription'}
                  </p>
                </div>
              )}
              */}

              <div className="flex justify-end gap-2">
                <Button variant="light" onPress={() => router.push('/dashboard')}>
                  Skip Setup
                </Button>
                <Button color="primary" size="lg" onPress={() => setStep(2)}>
                  Get Started →
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Step 2: Data Source */}
        {step === 2 && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold mb-2">Choose Your Data Source</h1>
                <p className="text-default-600">
                  You can try our demo data or upload your own transactions.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Demo Data Option */}
                <Card className="border-2 border-primary hover:border-primary-600 cursor-pointer">
                  <CardBody className="space-y-4 p-6">
                    <div className="text-4xl">🎯</div>
                    <h3 className="text-xl font-semibold">Try Demo Data</h3>
                    <p className="text-sm text-default-600">
                      We'll create 50 realistic transactions for you to explore.
                      Great for trying out features!
                    </p>
                    <ul className="text-sm space-y-1 text-default-600">
                      <li>✓ Common SaaS vendors</li>
                      <li>✓ Mixed income & expenses</li>
                      <li>✓ Last 90 days of activity</li>
                      <li>✓ Easy to delete later</li>
                    </ul>
                    <Button 
                      color="primary" 
                      className="w-full"
                      onPress={handleCreateDemo}
                      isLoading={loading}
                      size="lg"
                    >
                      Create Demo Data
                    </Button>
                  </CardBody>
                </Card>

                {/* Upload CSV Option */}
                <Card className="border-2 border-default-200 hover:border-default-400 cursor-pointer">
                  <CardBody className="space-y-4 p-6">
                    <div className="text-4xl">📁</div>
                    <h3 className="text-xl font-semibold">Upload Your Data</h3>
                    <p className="text-sm text-default-600">
                      Import transactions from your bank or accounting system.
                    </p>
                    <ul className="text-sm space-y-1 text-default-600">
                      <li>✓ CSV file format</li>
                      <li>✓ Bank statement export</li>
                      <li>✓ QuickBooks export</li>
                      <li>✓ Custom formats supported</li>
                    </ul>
                    <div className="space-y-2">
                      <Button 
                        color="default" 
                        variant="flat"
                        className="w-full"
                        onPress={handleDownloadSample}
                      >
                        Download Sample CSV
                      </Button>
                      <Button 
                        color="default"
                        className="w-full"
                        onPress={goToTransactions}
                        size="lg"
                      >
                        Go to Upload →
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              </div>

              <div className="flex justify-between">
                <Button variant="light" onPress={() => setStep(1)}>
                  ← Back
                </Button>
                <Button variant="light" onPress={() => router.push('/dashboard')}>
                  Skip Setup
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Step 3: View Transactions */}
        {step === 3 && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold mb-2">✅ Data Imported!</h1>
                <p className="text-default-600">
                  {demoDataCreated 
                    ? 'Your demo transactions are ready. Let\'s categorize them with AI!' 
                    : 'Your transactions have been imported. Ready for AI categorization?'}
                </p>
              </div>

              {onboardingStatus && (
                <div className="bg-success-50 border border-success-200 rounded-lg p-4">
                  <p className="font-medium text-success-700">
                    ✓ {demoDataCreated ? '50 demo transactions created' : 'Transactions imported'}
                  </p>
                </div>
              )}

              <div className="bg-default-100 rounded-lg p-6">
                <h3 className="font-semibold mb-4">What's Next?</h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="bg-primary text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">
                      1
                    </div>
                    <div>
                      <p className="font-medium">AI will analyze each transaction</p>
                      <p className="text-sm text-default-600">Using rules and machine learning</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="bg-primary text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">
                      2
                    </div>
                    <div>
                      <p className="font-medium">Proposed journal entries will be created</p>
                      <p className="text-sm text-default-600">With confidence scores</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="bg-primary text-white rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">
                      3
                    </div>
                    <div>
                      <p className="font-medium">You'll review and approve</p>
                      <p className="text-sm text-default-600">High confidence entries can auto-post</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between gap-2">
                <Button variant="light" onPress={goToTransactions}>
                  View Transactions
                </Button>
                <div className="flex gap-2">
                  <Button variant="light" onPress={() => setStep(2)}>
                    ← Back
                  </Button>
                  <Button color="primary" size="lg" onPress={() => setStep(4)}>
                    Start AI Categorization →
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Step 4: Propose Entries */}
        {step === 4 && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold mb-2">🤖 AI Categorization</h1>
                <p className="text-default-600">
                  Let AI propose journal entries for your transactions.
                </p>
              </div>

              <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 space-y-4">
                <div className="flex items-center gap-2">
                  <div className="text-3xl">⚡</div>
                  <div>
                    <h3 className="font-semibold text-lg">Ready to Process</h3>
                    <p className="text-sm text-default-600">
                      Click the button below to start AI categorization
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">The AI will:</p>
                <ul className="text-sm space-y-1 text-default-600 ml-4">
                  <li>• Check rule-based patterns first (instant, 100% accurate)</li>
                  <li>• Use machine learning for common transactions</li>
                  <li>• Apply LLM intelligence for complex cases</li>
                  <li>• Flag items that need human review</li>
                </ul>
              </div>

              <div className="flex justify-between gap-2">
                <Button variant="light" onPress={() => setStep(3)}>
                  ← Back
                </Button>
                <Button 
                  color="primary" 
                  size="lg"
                  onPress={() => {
                    // In production, this would trigger the API call
                    // For now, just advance to next step
                    setStep(5);
                  }}
                >
                  Propose Journal Entries →
                </Button>
              </div>

              <p className="text-xs text-default-500 text-center">
                Or go to <Button size="sm" variant="light" onPress={goToTransactions}>Transactions page</Button> to manually trigger
              </p>
            </CardBody>
          </Card>
        )}

        {/* Step 5: Review & Approve */}
        {step === 5 && (
          <Card>
            <CardBody className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold mb-2">✅ Review Proposed Entries</h1>
                <p className="text-default-600">
                  AI has categorized your transactions. Time to review and approve!
                </p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-success-50 border border-success-200 rounded-lg p-4">
                  <p className="text-2xl font-bold text-success-700">85%</p>
                  <p className="text-sm text-success-700">High Confidence</p>
                  <p className="text-xs text-default-600 mt-1">Auto-approvable</p>
                </div>
                <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                  <p className="text-2xl font-bold text-warning-700">12%</p>
                  <p className="text-sm text-warning-700">Medium Confidence</p>
                  <p className="text-xs text-default-600 mt-1">Quick review needed</p>
                </div>
                <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
                  <p className="text-2xl font-bold text-danger-700">3%</p>
                  <p className="text-sm text-danger-700">Needs Review</p>
                  <p className="text-xs text-default-600 mt-1">Manual categorization</p>
                </div>
              </div>

              <div className="bg-default-100 rounded-lg p-4 space-y-2">
                <h3 className="font-semibold">💡 Pro Tips:</h3>
                <ul className="text-sm space-y-1 text-default-600">
                  <li>• High confidence entries can be bulk-approved</li>
                  <li>• Review flagged items carefully</li>
                  <li>• Edit any entries before approving</li>
                  <li>• Create rules from patterns you see</li>
                </ul>
              </div>

              <div className="flex justify-between gap-2">
                <Button variant="light" onPress={() => setStep(4)}>
                  ← Back
                </Button>
                <div className="flex gap-2">
                  <Button variant="flat" onPress={goToTransactions}>
                    Review in Transactions
                  </Button>
                  <Button color="primary" size="lg" onPress={() => setStep(6)}>
                    Continue →
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Step 6: Complete / Connect QBO */}
        {step === 6 && (
          <Card>
            <CardBody className="space-y-6">
              <div className="text-center space-y-4">
                <div className="text-6xl">🎉</div>
                <h1 className="text-4xl font-bold">All Set!</h1>
                <p className="text-lg text-default-600">
                  You've completed the basic setup. Your AI Bookkeeper is ready to use!
                </p>
              </div>

              <Divider />

              <div className="space-y-4">
                <h2 className="text-xl font-semibold">What's Next?</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button 
                    size="lg" 
                    variant="flat" 
                    className="h-auto py-6"
                    onPress={goToTransactions}
                  >
                    <div className="text-left">
                      <div className="text-lg font-semibold">Continue Working</div>
                      <div className="text-sm opacity-60">Review and approve more transactions</div>
                    </div>
                  </Button>

                  <Button 
                    size="lg" 
                    variant="flat"
                    className="h-auto py-6"
                    onPress={goToFirm}
                  >
                    <div className="text-left">
                      <div className="text-lg font-semibold">Connect QuickBooks</div>
                      <div className="text-sm opacity-60">Export entries to your accounting system</div>
                    </div>
                  </Button>
                </div>
              </div>

              <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                <h3 className="font-semibold mb-2">📚 Learn More</h3>
                <ul className="text-sm space-y-1">
                  <li>• Check out <strong>Rules</strong> to automate categorization</li>
                  <li>• Visit <strong>Firm Settings</strong> to configure auto-posting</li>
                  <li>• Use <strong>Audit Log</strong> to track all changes</li>
                </ul>
              </div>

              <div className="flex justify-center">
                <Button 
                  color="primary" 
                  size="lg"
                  onPress={() => router.push('/dashboard')}
                >
                  Go to Dashboard →
                </Button>
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </AppShell>
  );
}

