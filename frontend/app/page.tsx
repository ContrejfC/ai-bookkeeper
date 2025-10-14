import { Button, Link, Card, CardBody } from "@nextui-org/react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-success/5 to-warning/5">
      {/* Header */}
      <header className="border-b border-divider/50 backdrop-blur-sm bg-background/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <span className="text-2xl">📒</span>
              <span className="text-xl font-bold">AI Bookkeeper</span>
            </div>
            <div className="flex items-center gap-3">
              <Button
                as={Link}
                href="/login"
                variant="light"
                size="md"
              >
                Log in
              </Button>
              <Button
                as={Link}
                href="/signup"
                color="primary"
                size="md"
              >
                Sign up
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="pt-20 pb-16 text-center">
          <div className="mb-6">
            <span className="text-6xl mb-4 inline-block">📒</span>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-primary to-success bg-clip-text text-transparent">
            AI Bookkeeper
          </h1>
          
          <p className="text-xl sm:text-2xl text-foreground/60 mb-8 max-w-3xl mx-auto">
            Calibrated, explainable bookkeeping automation powered by machine learning
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button
              as={Link}
              href="/signup"
              color="primary"
              size="lg"
              className="text-lg px-8 py-6 font-semibold"
            >
              Get Started Free
            </Button>
            <Button
              as={Link}
              href="/login"
              variant="bordered"
              size="lg"
              className="text-lg px-8 py-6"
            >
              Sign In
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="flex flex-wrap justify-center gap-6 text-sm text-foreground/40 mb-16">
            <div className="flex items-center gap-2">
              <span>✓</span>
              <span>SOC 2 Compliant</span>
            </div>
            <div className="flex items-center gap-2">
              <span>✓</span>
              <span>Bank-Grade Security</span>
            </div>
            <div className="flex items-center gap-2">
              <span>✓</span>
              <span>Free Tier Available</span>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="py-16">
          <h2 className="text-3xl font-bold text-center mb-12">Why AI Bookkeeper?</h2>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">🤖</div>
                <h3 className="text-xl font-semibold mb-2">AI-Powered</h3>
                <p className="text-foreground/60">
                  Machine learning categorizes transactions with calibrated confidence scores
                </p>
              </CardBody>
            </Card>

            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold mb-2">Explainable</h3>
                <p className="text-foreground/60">
                  Every decision includes reasoning - know why the AI chose each category
                </p>
              </CardBody>
            </Card>

            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-xl font-semibold mb-2">Automated</h3>
                <p className="text-foreground/60">
                  Automatic posting with safety thresholds and human-in-the-loop review
                </p>
              </CardBody>
            </Card>

            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-xl font-semibold mb-2">Real-Time Insights</h3>
                <p className="text-foreground/60">
                  Live metrics, automation rates, and financial reports at your fingertips
                </p>
              </CardBody>
            </Card>

            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">🔐</div>
                <h3 className="text-xl font-semibold mb-2">Audit Ready</h3>
                <p className="text-foreground/60">
                  Complete decision audit log, SOC 2 compliance, and evidence automation
                </p>
              </CardBody>
            </Card>

            <Card className="rounded-2xl">
              <CardBody className="p-6">
                <div className="text-4xl mb-4">🚀</div>
                <h3 className="text-xl font-semibold mb-2">Integrations</h3>
                <p className="text-foreground/60">
                  QuickBooks, Xero, and more - export to your favorite accounting software
                </p>
              </CardBody>
            </Card>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-16 text-center">
          <Card className="rounded-3xl max-w-4xl mx-auto bg-gradient-to-br from-primary/10 to-success/10">
            <CardBody className="p-12">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Ready to automate your bookkeeping?
              </h2>
              <p className="text-lg text-foreground/60 mb-8 max-w-2xl mx-auto">
                Join hundreds of businesses saving hours every week with intelligent automation
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  as={Link}
                  href="/signup"
                  color="primary"
                  size="lg"
                  className="text-lg px-8 py-6 font-semibold"
                >
                  Start Free Trial
                </Button>
                <Button
                  as={Link}
                  href="/login"
                  variant="bordered"
                  size="lg"
                  className="text-lg px-8 py-6"
                >
                  Sign In
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-divider/50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-sm text-foreground/60">
              © 2025 AI Bookkeeper. All rights reserved.
            </div>
            <div className="flex gap-6 text-sm">
              <Link href="#" className="text-foreground/60 hover:text-foreground">
                Privacy Policy
              </Link>
              <Link href="#" className="text-foreground/60 hover:text-foreground">
                Terms of Service
              </Link>
              <Link href="#" className="text-foreground/60 hover:text-foreground">
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
