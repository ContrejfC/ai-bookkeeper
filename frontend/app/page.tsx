"use client";

import { Button, Link, Card, CardBody } from "@nextui-org/react";
import { motion } from "framer-motion";

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

const features = [
  {
    icon: "🤖",
    title: "AI-Powered",
    description: "Machine learning categorizes transactions with calibrated confidence scores",
    gradient: "from-blue-500/10 to-cyan-500/10"
  },
  {
    icon: "🔍",
    title: "Explainable",
    description: "Every decision includes reasoning - know why the AI chose each category",
    gradient: "from-purple-500/10 to-pink-500/10"
  },
  {
    icon: "⚡",
    title: "Automated",
    description: "Automatic posting with safety thresholds and human-in-the-loop review",
    gradient: "from-yellow-500/10 to-orange-500/10"
  },
  {
    icon: "📊",
    title: "Real-Time Insights",
    description: "Live metrics, automation rates, and financial reports at your fingertips",
    gradient: "from-green-500/10 to-emerald-500/10"
  },
  {
    icon: "🔐",
    title: "Audit Ready",
    description: "Complete decision audit log, SOC 2 compliance, and evidence automation",
    gradient: "from-red-500/10 to-rose-500/10"
  },
  {
    icon: "🚀",
    title: "Integrations",
    description: "QuickBooks, Xero, and more - export to your favorite accounting software",
    gradient: "from-indigo-500/10 to-violet-500/10"
  }
];

const stats = [
  { value: "92%", label: "Automation Rate" },
  { value: "5hrs", label: "Saved Weekly" },
  { value: "500+", label: "Active Users" },
  { value: "99.9%", label: "Uptime" }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-success/5 relative overflow-hidden">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-warning/5 rounded-full blur-3xl"
          animate={{
            x: [-100, 100, -100],
            y: [-50, 50, -50],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <motion.header
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="border-b border-divider/50 backdrop-blur-md bg-background/60 sticky top-0 z-50"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <motion.div
                className="flex items-center gap-2"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <span className="text-2xl">📒</span>
                <span className="text-xl font-bold bg-gradient-to-r from-primary to-success bg-clip-text text-transparent">
                  AI Bookkeeper
                </span>
              </motion.div>
              <div className="flex items-center gap-3">
                <Button
                  as={Link}
                  href="/login"
                  variant="light"
                  size="md"
                  className="hover:scale-105 transition-transform"
                >
                  Log in
                </Button>
                <Button
                  as={Link}
                  href="/signup"
                  color="primary"
                  size="md"
                  className="font-semibold shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all"
                >
                  Sign up
                </Button>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Hero Section */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="pt-20 pb-16 text-center">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", duration: 1 }}
              className="mb-6 inline-block"
            >
              <motion.span
                className="text-7xl inline-block"
                animate={{
                  rotateY: [0, 360],
                }}
                transition={{
                  duration: 20,
                  repeat: Infinity,
                  ease: "linear"
                }}
              >
                📒
              </motion.span>
            </motion.div>
            
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6"
            >
              <span className="bg-gradient-to-r from-primary via-success to-warning bg-clip-text text-transparent animate-gradient bg-300%">
                AI Bookkeeper
              </span>
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-xl sm:text-2xl text-foreground/60 mb-8 max-w-3xl mx-auto"
            >
              Calibrated, explainable bookkeeping automation powered by machine learning
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
            >
              <Button
                as={Link}
                href="/signup"
                color="primary"
                size="lg"
                className="text-lg px-8 py-6 font-semibold shadow-2xl shadow-primary/30 hover:shadow-3xl hover:shadow-primary/40 hover:scale-110 transition-all"
              >
                Get Started Free
              </Button>
              <Button
                as={Link}
                href="/login"
                variant="bordered"
                size="lg"
                className="text-lg px-8 py-6 hover:scale-105 transition-transform"
              >
                Sign In
              </Button>
            </motion.div>

            {/* Trust Indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="flex flex-wrap justify-center gap-6 text-sm text-foreground/40 mb-16"
            >
              {["SOC 2 Compliant", "Bank-Grade Security", "Free Tier Available"].map((item, i) => (
                <motion.div
                  key={item}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.8 + i * 0.1 }}
                  className="flex items-center gap-2"
                >
                  <span className="text-success">✓</span>
                  <span>{item}</span>
                </motion.div>
              ))}
            </motion.div>
          </div>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="mb-20"
          >
            <Card className="rounded-3xl shadow-xl border border-divider/50 bg-gradient-to-br from-background/95 to-background/80 backdrop-blur-xl">
              <CardBody className="p-8">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                  {stats.map((stat, i) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 1.2 + i * 0.1, type: "spring" }}
                      className="text-center"
                    >
                      <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-primary to-success bg-clip-text text-transparent mb-2">
                        {stat.value}
                      </div>
                      <div className="text-sm text-foreground/60">{stat.label}</div>
                    </motion.div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </motion.div>

          {/* Features Grid */}
          <div className="py-16">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl font-bold text-center mb-4"
            >
              Why AI Bookkeeper?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-center text-foreground/60 mb-12 max-w-2xl mx-auto"
            >
              Everything you need to automate your bookkeeping with confidence
            </motion.p>
            
            <motion.div
              variants={staggerContainer}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto"
            >
              {features.map((feature, i) => (
                <motion.div
                  key={feature.title}
                  variants={fadeInUp}
                  whileHover={{
                    y: -8,
                    transition: { type: "spring", stiffness: 300 }
                  }}
                >
                  <Card className={`rounded-2xl border border-divider/50 shadow-lg hover:shadow-2xl transition-shadow bg-gradient-to-br ${feature.gradient} backdrop-blur-sm h-full`}>
                    <CardBody className="p-6">
                      <motion.div
                        className="text-5xl mb-4"
                        whileHover={{ scale: 1.2, rotate: 10 }}
                        transition={{ type: "spring", stiffness: 400 }}
                      >
                        {feature.icon}
                      </motion.div>
                      <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                      <p className="text-foreground/60 text-sm leading-relaxed">
                        {feature.description}
                      </p>
                    </CardBody>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>

          {/* How It Works Section */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="py-20"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-center mb-16">
              How It Works
            </h2>
            
            <div className="max-w-5xl mx-auto">
              {[
                { step: "1", title: "Upload Transactions", desc: "Import from your bank, credit cards, or accounting software" },
                { step: "2", title: "AI Reviews & Categorizes", desc: "Our ML model analyzes and categorizes each transaction with confidence scores" },
                { step: "3", title: "Review & Approve", desc: "Low-confidence items flagged for your review with explanations" },
                { step: "4", title: "Export & Post", desc: "Approved entries posted to your ledger or exported to QuickBooks/Xero" }
              ].map((item, i) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -50 : 50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                  className="flex gap-6 mb-12 last:mb-0"
                >
                  <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-primary to-success flex items-center justify-center text-white font-bold text-xl shadow-lg"
                  >
                    {item.step}
                  </motion.div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                    <p className="text-foreground/60">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Social Proof */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="py-16 text-center"
          >
            <p className="text-sm text-foreground/40 mb-8">TRUSTED BY</p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-40">
              <div className="text-2xl font-bold">StartupCo</div>
              <div className="text-2xl font-bold">TechFirm</div>
              <div className="text-2xl font-bold">Consultants Inc</div>
              <div className="text-2xl font-bold">SMB Solutions</div>
            </div>
          </motion.div>

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="py-20 text-center"
          >
            <Card className="rounded-3xl max-w-4xl mx-auto shadow-2xl border-2 border-primary/20 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-success/10 to-warning/10" />
              <CardBody className="p-12 relative">
                <motion.div
                  initial={{ scale: 0.9 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ type: "spring" }}
                >
                  <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                    Ready to automate your bookkeeping?
                  </h2>
                  <p className="text-lg text-foreground/60 mb-8 max-w-2xl mx-auto">
                    Join hundreds of businesses saving hours every week with intelligent automation
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Button
                        as={Link}
                        href="/signup"
                        color="primary"
                        size="lg"
                        className="text-lg px-8 py-6 font-semibold shadow-xl shadow-primary/40"
                      >
                        Start Free Trial
                      </Button>
                    </motion.div>
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Button
                        as={Link}
                        href="/login"
                        variant="bordered"
                        size="lg"
                        className="text-lg px-8 py-6"
                      >
                        Sign In
                      </Button>
                    </motion.div>
                  </div>
                  
                  {/* Trial Badge */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 }}
                    className="mt-6 text-sm text-foreground/60"
                  >
                    <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-success/10 border border-success/20">
                      <span className="text-success">✓</span>
                      No credit card required • Free forever tier
                    </span>
                  </motion.div>
                </motion.div>
              </CardBody>
            </Card>
          </motion.div>

          {/* Testimonials */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="py-16"
          >
            <h2 className="text-3xl font-bold text-center mb-12">What Our Users Say</h2>
            <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {[
                {
                  quote: "Cut our monthly close time from 2 days to 4 hours. Game changer!",
                  author: "Sarah Chen",
                  role: "CFO, TechStartup"
                },
                {
                  quote: "The explainability feature gives me confidence in every automated decision.",
                  author: "Mike Rodriguez",
                  role: "Accountant, SMB Solutions"
                },
                {
                  quote: "SOC 2 compliance made our audit a breeze. Highly recommend.",
                  author: "Emily Taylor",
                  role: "COO, FinanceGroup"
                }
              ].map((testimonial, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                  whileHover={{ y: -5 }}
                >
                  <Card className="rounded-2xl shadow-lg border border-divider/50 h-full">
                    <CardBody className="p-6">
                      <div className="text-4xl mb-4 opacity-20">"</div>
                      <p className="text-foreground/80 mb-6 italic">{testimonial.quote}</p>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-success flex items-center justify-center text-white font-bold">
                          {testimonial.author[0]}
                        </div>
                        <div>
                          <div className="font-semibold text-sm">{testimonial.author}</div>
                          <div className="text-xs text-foreground/60">{testimonial.role}</div>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="border-t border-divider/50 mt-16 bg-background/60 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">📒</span>
                  <span className="font-bold">AI Bookkeeper</span>
                </div>
                <p className="text-sm text-foreground/60">
                  Intelligent automation for modern accounting teams
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3">Product</h4>
                <div className="flex flex-col gap-2 text-sm text-foreground/60">
                  <Link href="#" className="hover:text-foreground">Features</Link>
                  <Link href="#" className="hover:text-foreground">Pricing</Link>
                  <Link href="#" className="hover:text-foreground">Integrations</Link>
                  <Link href="#" className="hover:text-foreground">API Docs</Link>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3">Company</h4>
                <div className="flex flex-col gap-2 text-sm text-foreground/60">
                  <Link href="#" className="hover:text-foreground">About</Link>
                  <Link href="#" className="hover:text-foreground">Blog</Link>
                  <Link href="#" className="hover:text-foreground">Careers</Link>
                  <Link href="#" className="hover:text-foreground">Contact</Link>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3">Legal</h4>
                <div className="flex flex-col gap-2 text-sm text-foreground/60">
                  <Link href="#" className="hover:text-foreground">Privacy Policy</Link>
                  <Link href="#" className="hover:text-foreground">Terms of Service</Link>
                  <Link href="#" className="hover:text-foreground">Security</Link>
                  <Link href="#" className="hover:text-foreground">Compliance</Link>
                </div>
              </div>
            </div>
            
            <div className="border-t border-divider/50 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="text-sm text-foreground/60">
                © 2025 AI Bookkeeper. All rights reserved.
              </div>
              <div className="flex gap-4">
                {["Twitter", "LinkedIn", "GitHub"].map((social) => (
                  <Link
                    key={social}
                    href="#"
                    className="text-foreground/60 hover:text-foreground text-sm"
                  >
                    {social}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </footer>
      </div>

      <style jsx global>{`
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .animate-gradient {
          background-size: 300% 300%;
          animation: gradient 6s ease infinite;
        }
        .bg-300\% {
          background-size: 300% 300%;
        }
      `}</style>
    </div>
  );
}
