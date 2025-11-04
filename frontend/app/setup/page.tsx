"use client";

import { useState } from "react";
import { Button, Link, Card, CardBody, CardHeader, Accordion, AccordionItem, Chip, Code } from "@nextui-org/react";
import { motion } from "framer-motion";

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
};

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <Button
      size="sm"
      color={copied ? "success" : "default"}
      variant="flat"
      onClick={handleCopy}
      className="ml-2"
    >
      {copied ? "Copied!" : "Copy"}
    </Button>
  );
};

const CodeBlock = ({ code, language = "bash" }: { code: string; language?: string }) => (
  <div className="bg-gray-900 rounded-lg p-4 my-4 overflow-x-auto">
    <div className="flex justify-between items-start mb-2">
      <span className="text-xs text-gray-400 uppercase">{language}</span>
      <CopyButton text={code} />
    </div>
    <pre className="text-sm text-gray-100">
      <code>{code}</code>
    </pre>
  </div>
);

export default function SetupPage() {
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const toggleStep = (step: number) => {
    setCompletedSteps(prev =>
      prev.includes(step) ? prev.filter(s => s !== step) : [...prev, step]
    );
  };

  const steps = [
    {
      title: "Get Your Vercel Token",
      content: (
        <>
          <p className="text-gray-300 mb-4">Create an API token from your Vercel account.</p>
          
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">1</div>
              <div>
                <p className="text-gray-200">Go to Vercel Dashboard</p>
                <Link href="https://vercel.com/account/tokens" target="_blank" className="text-sm text-emerald-400 hover:text-emerald-300">
                  https://vercel.com/account/tokens
                </Link>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">2</div>
              <p className="text-gray-200">Click <strong>"Create Token"</strong></p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">3</div>
              <p className="text-gray-200">Name it: <Code>GitHub Actions Deployment</Code></p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">4</div>
              <div>
                <p className="text-gray-200 mb-2">⚠️ Copy the token immediately (you won&apos;t see it again!)</p>
                <p className="text-sm text-gray-400">Token format: <Code className="text-xs">vercel_xxxxx...</Code></p>
              </div>
            </div>
          </div>
        </>
      )
    },
    {
      title: "Get Vercel Org ID and Project ID",
      content: (
        <>
          <p className="text-gray-300 mb-4">Use Vercel CLI to link your project and get the required IDs.</p>
          
          <CodeBlock code={`# Navigate to frontend directory
cd /Users/fabiancontreras/ai-bookkeeper/frontend

# Install Vercel CLI globally
npm install -g vercel@latest

# Link the project
vercel link`} />
          
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-300 mb-2"><strong>What happens:</strong></p>
            <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
              <li>Login if needed (browser will open)</li>
              <li>Type <Code className="text-xs">N</Code> for &quot;Set up and deploy?&quot;</li>
              <li>Select your organization/account</li>
              <li>Type <Code className="text-xs">Y</Code> for &quot;Link to existing project?&quot;</li>
              <li>Select <strong>ai-bookkeeper</strong></li>
            </ul>
          </div>
          
          <p className="text-gray-300 mb-2">Get the IDs:</p>
          <CodeBlock code="cat .vercel/project.json" />
          
          <p className="text-sm text-gray-400 mb-2">You&apos;ll see:</p>
          <CodeBlock language="json" code={`{
  "orgId": "team_abc123xyz",
  "projectId": "prj_abc123xyz"
}`} />
          
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
            <p className="text-sm text-emerald-300">✅ Copy both <Code className="text-xs">orgId</Code> and <Code className="text-xs">projectId</Code> values</p>
          </div>
        </>
      )
    },
    {
      title: "Add GitHub Secrets",
      content: (
        <>
          <p className="text-gray-300 mb-4">Add the three required secrets to your GitHub repository.</p>
          
          <Link 
            href="https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions" 
            target="_blank"
            className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-400 px-4 py-2 rounded-lg hover:bg-emerald-500/30 mb-6"
          >
            <span>Open GitHub Secrets Page</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </Link>
          
          <div className="space-y-4">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-2">Secret 1: VERCEL_TOKEN</h4>
              <p className="text-sm text-gray-400">Paste the token from Step 1</p>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-2">Secret 2: VERCEL_ORG_ID</h4>
              <p className="text-sm text-gray-400">Paste the <Code className="text-xs">orgId</Code> from Step 2</p>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h4 className="text-white font-semibold mb-2">Secret 3: VERCEL_PROJECT_ID</h4>
              <p className="text-sm text-gray-400">Paste the <Code className="text-xs">projectId</Code> from Step 2</p>
            </div>
          </div>
        </>
      )
    },
    {
      title: "Trigger Deployment",
      content: (
        <>
          <p className="text-gray-300 mb-4">Manually run the deployment workflow for the first time.</p>
          
          <Link 
            href="https://github.com/ContrejfC/ai-bookkeeper/actions" 
            target="_blank"
            className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-400 px-4 py-2 rounded-lg hover:bg-emerald-500/30 mb-6"
          >
            <span>Open GitHub Actions</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </Link>
          
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">1</div>
              <p className="text-gray-200">Click on <strong>&quot;Deploy Prod (Monorepo)&quot;</strong> in the left sidebar</p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">2</div>
              <p className="text-gray-200">Click <strong>&quot;Run workflow&quot;</strong> button (top right)</p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">3</div>
              <p className="text-gray-200">Ensure <Code className="text-xs">main</Code> branch is selected</p>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold">4</div>
              <p className="text-gray-200">Click the green <strong>&quot;Run workflow&quot;</strong> button</p>
            </div>
          </div>
          
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 mt-6">
            <p className="text-sm text-yellow-300">⏰ Deployment takes about 3-5 minutes</p>
          </div>
        </>
      )
    },
    {
      title: "Monitor & Verify",
      content: (
        <>
          <p className="text-gray-300 mb-4">Watch the workflow run and verify all steps complete successfully.</p>
          
          <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
            <h4 className="text-white font-semibold mb-3">Expected Workflow Steps:</h4>
            <div className="space-y-2 text-sm">
              {[
                "Checkout repository",
                "Setup Node.js",
                "Install Vercel CLI",
                "Pull Vercel environment",
                "Build project artifacts",
                "Deploy to production",
                "Force alias to domain",
                "Smoke: Policy dates",
                "Smoke: SOC2 copy",
                "Smoke: API guards",
                "Smoke: UI controls",
                "Smoke: Provenance endpoints"
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-2 text-gray-300">
                  <div className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckIcon />
                  </div>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
            <p className="text-sm text-emerald-300"><strong>✅ Success:</strong> All steps green means deployment is live!</p>
          </div>
        </>
      )
    },
    {
      title: "Test Production Endpoints",
      content: (
        <>
          <p className="text-gray-300 mb-4">Verify the deployment by testing the provenance endpoints.</p>
          
          <div className="space-y-4">
            <div>
              <h4 className="text-white font-semibold mb-2">Test 1: Version Endpoint</h4>
              <CodeBlock code="curl -s https://ai-bookkeeper-nine.vercel.app/api-version | jq ." />
              <p className="text-sm text-gray-400">✅ Should return JSON with commit SHA, environment, and build info</p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-2">Test 2: Smoke Test Endpoint</h4>
              <CodeBlock code="curl -s https://ai-bookkeeper-nine.vercel.app/api-smoke | jq ." />
              <p className="text-sm text-gray-400">✅ All assertions should be <Code className="text-xs">true</Code></p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-2">Test 3: UI Build Tag</h4>
              <Link 
                href="https://ai-bookkeeper-nine.vercel.app/free/categorizer?verify=1" 
                target="_blank"
                className="text-emerald-400 hover:text-emerald-300 text-sm"
              >
                Visit: /free/categorizer?verify=1
              </Link>
              <p className="text-sm text-gray-400 mt-2">✅ Look for a small tag in the bottom-right corner with commit SHA</p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-2">Test 4: Local Smoke Tests</h4>
              <CodeBlock code={`cd /Users/fabiancontreras/ai-bookkeeper
npm run smoke:prod`} />
              <p className="text-sm text-gray-400">✅ Should exit with code 0 and show all tests passed</p>
            </div>
          </div>
        </>
      )
    }
  ];

  const progressPercent = (completedSteps.length / steps.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              AI Bookkeeper
            </Link>
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <motion.div
        className="container mx-auto px-6 py-16"
        initial="initial"
        animate="animate"
        variants={fadeInUp}
      >
        <div className="max-w-4xl mx-auto text-center mb-12">
          <Chip color="success" variant="flat" className="mb-4">
            Deployment Setup
          </Chip>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent mb-6">
            Deploy to Production
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            Step-by-step guide to deploy AI Bookkeeper with automated CI/CD, provenance verification, and comprehensive smoke tests.
          </p>
          
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Progress</span>
              <span>{completedSteps.length} of {steps.length} steps completed</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500"
                initial={{ width: 0 }}
                animate={{ width: `${progressPercent}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>

        {/* Steps */}
        <div className="max-w-4xl mx-auto">
          <Accordion
            variant="splitted"
            className="gap-4"
          >
            {steps.map((step, index) => (
              <AccordionItem
                key={index}
                aria-label={step.title}
                title={
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 text-white font-bold text-sm">
                      {completedSteps.includes(index) ? <CheckIcon /> : index + 1}
                    </div>
                    <span className="font-semibold text-white">{step.title}</span>
                  </div>
                }
                className="bg-gray-800/50 border border-gray-700/50 rounded-lg"
                indicator={
                  <Button
                    size="sm"
                    color={completedSteps.includes(index) ? "success" : "default"}
                    variant="flat"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleStep(index);
                    }}
                  >
                    {completedSteps.includes(index) ? "Done" : "Mark as Done"}
                  </Button>
                }
              >
                <div className="px-4 pb-4">
                  {step.content}
                </div>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        {/* Success Checklist */}
        <motion.div
          className="max-w-4xl mx-auto mt-12"
          variants={fadeInUp}
        >
          <Card className="bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20">
            <CardHeader>
              <h3 className="text-2xl font-bold text-white">✅ Success Checklist</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                {[
                  "Vercel token created and stored",
                  "VERCEL_ORG_ID and VERCEL_PROJECT_ID copied",
                  "All 3 GitHub secrets added",
                  "Workflow ran successfully (all green checks)",
                  "/api-version returns JSON with commit SHA",
                  "/api-smoke returns all assertions true",
                  "UI build tag appears on ?verify=1",
                  "npm run smoke:prod passes locally",
                  "Automatic deployments working on push to main"
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3 text-gray-200">
                    <div className="mt-1 flex-shrink-0 w-5 h-5 rounded border-2 border-emerald-400/50" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </motion.div>

        {/* Quick Reference */}
        <motion.div
          className="max-w-4xl mx-auto mt-12"
          variants={fadeInUp}
        >
          <Card className="bg-gray-800/50 border border-gray-700/50">
            <CardHeader>
              <h3 className="text-2xl font-bold text-white">📞 Quick Reference</h3>
            </CardHeader>
            <CardBody>
              <div className="grid md:grid-cols-2 gap-4">
                <Link href="https://github.com/ContrejfC/ai-bookkeeper/settings/secrets/actions" target="_blank" className="text-emerald-400 hover:text-emerald-300">
                  GitHub Secrets →
                </Link>
                <Link href="https://github.com/ContrejfC/ai-bookkeeper/actions" target="_blank" className="text-emerald-400 hover:text-emerald-300">
                  GitHub Actions →
                </Link>
                <Link href="https://vercel.com/account/tokens" target="_blank" className="text-emerald-400 hover:text-emerald-300">
                  Vercel Tokens →
                </Link>
                <Link href="https://ai-bookkeeper-nine.vercel.app" target="_blank" className="text-emerald-400 hover:text-emerald-300">
                  Production URL →
                </Link>
              </div>
            </CardBody>
          </Card>
        </motion.div>

        {/* Need Help */}
        <div className="max-w-4xl mx-auto mt-12 text-center">
          <p className="text-gray-400">
            Need help? Check the detailed documentation in{" "}
            <Link href="https://github.com/ContrejfC/ai-bookkeeper/blob/main/STEP_BY_STEP_DEPLOYMENT.md" target="_blank" className="text-emerald-400 hover:text-emerald-300">
              STEP_BY_STEP_DEPLOYMENT.md
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}

