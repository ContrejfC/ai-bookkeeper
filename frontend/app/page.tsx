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

// SVG Icon Components
const AIIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#06b6d4" />
      </linearGradient>
    </defs>
    <rect x="3" y="4" width="18" height="12" rx="2" fill="url(#aiGradient)" />
    <rect x="5" y="7" width="14" height="6" rx="1" fill="white" opacity="0.9" />
    <circle cx="8" cy="10" r="1" fill="url(#aiGradient)" />
    <circle cx="16" cy="10" r="1" fill="url(#aiGradient)" />
    <path d="M8 12h8" stroke="url(#aiGradient)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="searchGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <circle cx="11" cy="11" r="8" fill="url(#searchGradient)" />
    <path d="m21 21-4.35-4.35" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <circle cx="11" cy="11" r="3" fill="white" opacity="0.8" />
  </svg>
);

const AutomationIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="autoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06b6d4" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="url(#autoGradient)" />
    <circle cx="12" cy="12" r="2" fill="white" opacity="0.9" />
  </svg>
);

const AnalyticsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="analyticsGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
    </defs>
    <rect x="3" y="16" width="4" height="5" rx="1" fill="url(#analyticsGradient)" />
    <rect x="8" y="12" width="4" height="9" rx="1" fill="url(#analyticsGradient)" />
    <rect x="13" y="8" width="4" height="13" rx="1" fill="url(#analyticsGradient)" />
    <rect x="18" y="4" width="4" height="17" rx="1" fill="url(#analyticsGradient)" />
    <path d="M5 16h14" stroke="white" strokeWidth="1" opacity="0.6" />
  </svg>
);

const SecurityIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="securityGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <path d="M12 2l8 4v6c0 5.55-3.84 10.74-9 12-5.16-1.26-9-6.45-9-12V6l8-4z" fill="url(#securityGradient)" />
    <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const IntegrationIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-12 h-12">
    <defs>
      <linearGradient id="integrationGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#0891b2" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <rect x="2" y="6" width="20" height="12" rx="2" fill="url(#integrationGradient)" />
    <circle cx="8" cy="12" r="2" fill="white" opacity="0.9" />
    <circle cx="16" cy="12" r="2" fill="white" opacity="0.9" />
    <path d="M10 12h4" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M3 9h3M3 15h3M18 9h3M18 15h3" stroke="white" strokeWidth="1" opacity="0.6" />
  </svg>
);

const features = [
  {
    icon: AIIcon,
    title: "AI-Powered",
    description: "Machine learning categorizes transactions with calibrated confidence scores",
    gradient: "from-emerald-500/10 to-teal-500/10"
  },
  {
    icon: SearchIcon,
    title: "Explainable",
    description: "Every decision includes reasoning - know why the AI chose each category",
    gradient: "from-teal-500/10 to-cyan-500/10"
  },
  {
    icon: AutomationIcon,
    title: "Automated",
    description: "Automatic posting with safety thresholds and human-in-the-loop review",
    gradient: "from-cyan-500/10 to-blue-500/10"
  },
  {
    icon: AnalyticsIcon,
    title: "Real-Time Insights",
    description: "Live metrics, automation rates, and financial reports at your fingertips",
    gradient: "from-green-500/10 to-emerald-500/10"
  },
  {
    icon: SecurityIcon,
    title: "Audit Ready",
    description: "Complete decision audit log, SOC 2 compliance, and evidence automation",
    gradient: "from-emerald-600/10 to-teal-600/10"
  },
  {
    icon: IntegrationIcon,
    title: "Integrations",
    description: "QuickBooks, Xero, and more - export to your favorite accounting software",
    gradient: "from-teal-600/10 to-cyan-600/10"
  }
];

const stats = [
  { value: "4-Tier", label: "AI Decision System" },
  { value: "CSV/OFX/PDF", label: "File Formats Supported" },
  { value: "QBO + Xero", label: "Integrations" },
  { value: "Live", label: "Production Status" }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-500/5 via-background to-cyan-500/5 relative overflow-hidden">
      {/* Flowing Pattern Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Animated SVG Pattern */}
        <motion.svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 1200 800"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2 }}
        >
          <defs>
            <linearGradient id="flowGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.3" />
            </linearGradient>
            <linearGradient id="flowGradient2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#059669" stopOpacity="0.3" />
              <stop offset="50%" stopColor="#0891b2" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.25" />
            </linearGradient>
            <linearGradient id="flowGradient3" x1="50%" y1="0%" x2="50%" y2="100%">
              <stop offset="0%" stopColor="#34d399" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          
          {/* Primary Flowing Curves */}
          <motion.path
            d="M0,400 Q200,200 400,400 T800,400 T1200,300"
            stroke="url(#flowGradient1)"
            strokeWidth="2"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.8 }}
            transition={{ duration: 8, ease: "easeInOut" }}
          />
          
          <motion.path
            d="M0,300 Q300,500 600,300 T1200,400"
            stroke="url(#flowGradient2)"
            strokeWidth="1.5"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.6 }}
            transition={{ duration: 10, ease: "easeInOut", delay: 1 }}
          />
          
          <motion.path
            d="M0,500 Q150,300 350,500 Q550,700 750,500 Q950,300 1200,500"
            stroke="url(#flowGradient3)"
            strokeWidth="1"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.4 }}
            transition={{ duration: 12, ease: "easeInOut", delay: 2 }}
          />
          
          {/* Complex Wave Patterns */}
          <motion.path
            d="M0,600 Q250,400 500,600 Q750,800 1000,600 T1200,650"
            stroke="url(#flowGradient1)"
            strokeWidth="1"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.3 }}
            transition={{ duration: 14, ease: "easeInOut", delay: 3 }}
          />
          
          <motion.path
            d="M0,200 Q400,600 800,200 T1200,250"
            stroke="url(#flowGradient2)"
            strokeWidth="0.8"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.2 }}
            transition={{ duration: 16, ease: "easeInOut", delay: 4 }}
          />
          
          {/* Additional Complex Curves */}
          <motion.path
            d="M0,100 Q150,350 300,100 Q450,450 600,100 Q750,350 900,100 Q1050,450 1200,100"
            stroke="url(#flowGradient3)"
            strokeWidth="0.6"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.15 }}
            transition={{ duration: 18, ease: "easeInOut", delay: 5 }}
          />
          
          <motion.path
            d="M0,700 Q200,550 400,700 Q600,850 800,700 Q1000,550 1200,700"
            stroke="url(#flowGradient1)"
            strokeWidth="0.7"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.18 }}
            transition={{ duration: 20, ease: "easeInOut", delay: 6 }}
          />
          
          {/* Spiraling Patterns */}
          <motion.path
            d="M0,350 Q100,250 200,350 Q300,450 400,350 Q500,250 600,350 Q700,450 800,350 Q900,250 1000,350 Q1100,450 1200,350"
            stroke="url(#flowGradient2)"
            strokeWidth="0.5"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.12 }}
            transition={{ duration: 22, ease: "easeInOut", delay: 7 }}
          />
          
          <motion.path
            d="M0,550 Q120,450 240,550 Q360,650 480,550 Q600,450 720,550 Q840,650 960,550 Q1080,450 1200,550"
            stroke="url(#flowGradient3)"
            strokeWidth="0.4"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.1 }}
            transition={{ duration: 24, ease: "easeInOut", delay: 8 }}
          />
          
          {/* Organic Flow Patterns */}
          <motion.path
            d="M0,150 Q80,280 160,150 Q240,380 320,150 Q400,280 480,150 Q560,380 640,150 Q720,280 800,150 Q880,380 960,150 Q1040,280 1120,150 Q1200,380 1200,150"
            stroke="url(#flowGradient1)"
            strokeWidth="0.3"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.08 }}
            transition={{ duration: 26, ease: "easeInOut", delay: 9 }}
          />
          
          <motion.path
            d="M0,650 Q60,520 120,650 Q180,780 240,650 Q300,520 360,650 Q420,780 480,650 Q540,520 600,650 Q660,780 720,650 Q780,520 840,650 Q900,780 960,650 Q1020,520 1080,650 Q1140,780 1200,650"
            stroke="url(#flowGradient2)"
            strokeWidth="0.35"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.09 }}
            transition={{ duration: 28, ease: "easeInOut", delay: 10 }}
          />
          
          {/* Subtle Overlay Patterns */}
          <motion.path
            d="M0,250 Q200,180 400,250 Q600,320 800,250 Q1000,180 1200,250"
            stroke="url(#flowGradient3)"
            strokeWidth="0.25"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.06 }}
            transition={{ duration: 30, ease: "easeInOut", delay: 11 }}
          />
          
          <motion.path
            d="M0,450 Q300,380 600,450 Q900,520 1200,450"
            stroke="url(#flowGradient1)"
            strokeWidth="0.2"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.05 }}
            transition={{ duration: 32, ease: "easeInOut", delay: 12 }}
          />
        </motion.svg>

        {/* Animated Blobs Overlay */}
        <motion.div
          className="absolute -top-40 -right-40 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl"
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
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl"
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
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl"
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
        
        {/* Floating Particles - use fixed positions for hydration */}
        {[...Array(30)].map((_, i) => {
          // Generate consistent positions using index-based seeding
          const left = ((i * 37) % 100);
          const top = ((i * 53) % 100);
          const duration = 8 + ((i * 23) % 12);
          const delay = (i * 0.5) % 5;
          
          return (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-emerald-500/20 rounded-full"
              style={{
                left: `${left}%`,
                top: `${top}%`,
              }}
              animate={{
                y: [-30, 30, -30],
                x: [-10, 10, -10],
                opacity: [0.1, 0.6, 0.1],
                scale: [0.3, 1.2, 0.3],
              }}
              transition={{
                duration,
                repeat: Infinity,
                ease: "easeInOut",
                delay,
              }}
            />
          );
        })}
        
        {/* Additional Slow-Moving Particles - use fixed positions for hydration */}
        {[...Array(15)].map((_, i) => {
          // Generate consistent positions using index-based seeding
          const left = ((i * 41 + 13) % 100);
          const top = ((i * 67 + 19) % 100);
          const duration = 20 + ((i * 29) % 20);
          const delay = (i * 0.7) % 10;
          
          return (
            <motion.div
              key={`slow-${i}`}
              className="absolute w-0.5 h-0.5 bg-cyan-500/15 rounded-full"
              style={{
                left: `${left}%`,
                top: `${top}%`,
              }}
              animate={{
                y: [-50, 50, -50],
                x: [-20, 20, -20],
                opacity: [0.05, 0.3, 0.05],
                scale: [0.2, 0.8, 0.2],
              }}
              transition={{
                duration,
                repeat: Infinity,
                ease: "easeInOut",
                delay,
              }}
            />
          );
        })}
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
                <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-cyan-500 bg-clip-text text-transparent">
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
                  Sign In
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
              <span className="bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 bg-clip-text text-transparent animate-gradient bg-300%">
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
                className="text-lg px-8 py-6 font-semibold shadow-2xl shadow-emerald-500/30 hover:shadow-3xl hover:shadow-emerald-500/40 hover:scale-110 transition-all"
              >
                Create Account
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
              {["SOC 2 Controls", "PII Redaction", "JWT Auth + CSRF Protection"].map((item, i) => (
                <motion.div
                  key={item}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.8 + i * 0.1 }}
                  className="flex items-center gap-2"
                >
                  <span className="text-emerald-500">✓</span>
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
                      <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-emerald-500 to-cyan-500 bg-clip-text text-transparent mb-2">
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
          <div id="features" className="py-16">
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
                        className="mb-4 flex justify-center"
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        transition={{ type: "spring", stiffness: 400 }}
                      >
                        <feature.icon />
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
                { step: "1", title: "Upload Bank Statements", desc: "Upload CSV, OFX, or PDF files from your bank or credit card" },
                { step: "2", title: "4-Tier AI Categorization", desc: "Rules engine → Vector search → LLM reasoning → Human review (with confidence scores & explanations)" },
                { step: "3", title: "Review & Approve", desc: "See every AI decision with reasoning. Low-confidence items (<60%) automatically flagged for review" },
                { step: "4", title: "Export to QuickBooks or Xero", desc: "One-click OAuth2 export with idempotent posting (demo mode available for testing)" }
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
                    className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-white font-bold text-xl shadow-lg"
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

          {/* Use Cases */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="py-16 text-center"
          >
            <p className="text-sm text-foreground/40 mb-8">PERFECT FOR</p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">
              <div className="text-lg font-semibold">Small Businesses</div>
              <div className="text-lg font-semibold">Accountants</div>
              <div className="text-lg font-semibold">Startups</div>
              <div className="text-lg font-semibold">Freelancers</div>
            </div>
          </motion.div>

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="py-20 text-center"
          >
            <Card className="rounded-3xl max-w-4xl mx-auto shadow-2xl border-2 border-emerald-500/20 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-teal-500/10 to-cyan-500/10" />
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
                    Transform your bookkeeping workflow with AI-powered categorization and intelligent automation
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
                        className="text-lg px-8 py-6 font-semibold shadow-xl shadow-emerald-500/40"
                      >
                        Get Started
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
                  <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <span className="text-emerald-500">✓</span>
                      Live in production • QuickBooks & Xero integrations
                    </span>
                  </motion.div>
                </motion.div>
              </CardBody>
            </Card>
          </motion.div>

          {/* Real Features Showcase */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="py-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4">Built for Real Accounting Workflows</h2>
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-center text-foreground/60 mb-12 max-w-2xl mx-auto"
            >
              Enterprise-grade features for professional accounting teams
            </motion.p>
            
            <motion.div
              variants={staggerContainer}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto"
            >
              {[
                {
                  feature: "Multi-Tenant Architecture",
                  description: "Manage multiple companies/entities from a single account with role-based access control (owner, staff)",
                  icon: "🏢",
                  gradient: "from-emerald-500/10 to-teal-500/10"
                },
                {
                  feature: "Audit Trail & Compliance",
                  description: "Complete audit logging, PII redaction, request tracing, and SOC 2 control implementation",
                  icon: "📋",
                  gradient: "from-teal-500/10 to-cyan-500/10"
                },
                {
                  feature: "Idempotent Operations",
                  description: "Safe re-processing with duplicate detection, webhook idempotency, and 24-hour deduplication windows",
                  icon: "🔒",
                  gradient: "from-cyan-500/10 to-blue-500/10"
                }
              ].map((item, i) => (
                <motion.div
                  key={i}
                  variants={fadeInUp}
                  whileHover={{
                    y: -8,
                    transition: { type: "spring", stiffness: 300 }
                  }}
                >
                  <Card className={`rounded-2xl border border-divider/50 shadow-lg hover:shadow-2xl transition-shadow bg-gradient-to-br ${item.gradient} backdrop-blur-sm h-full`}>
                    <CardBody className="p-6">
                      <motion.div
                        className="text-4xl mb-4 flex justify-center"
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        transition={{ type: "spring", stiffness: 400 }}
                      >
                        {item.icon}
                      </motion.div>
                      <h3 className="text-xl font-semibold mb-2 text-center">{item.feature}</h3>
                      <p className="text-foreground/60 text-sm leading-relaxed">
                        {item.description}
                      </p>
                    </CardBody>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
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
                  <Link href="#features" className="hover:text-foreground">Features</Link>
                  <Link href="/pricing" className="hover:text-foreground">Pricing</Link>
                  <Link href="/dashboard" className="hover:text-foreground">Dashboard</Link>
                  <Link href="https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/docs" target="_blank" className="hover:text-foreground">API Docs</Link>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3">Resources</h4>
                <div className="flex flex-col gap-2 text-sm text-foreground/60">
                  <Link href="/welcome" className="hover:text-foreground">Getting Started</Link>
                  <Link href="/export" className="hover:text-foreground">QuickBooks Setup</Link>
                  <Link href="/rules" className="hover:text-foreground">Automation Rules</Link>
                  <Link href="https://github.com/ContrejfC/ai-bookkeeper" target="_blank" className="hover:text-foreground">GitHub</Link>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3">Legal</h4>
                <div className="flex flex-col gap-2 text-sm text-foreground/60">
                  <Link href="/privacy" className="hover:text-foreground">Privacy Policy</Link>
                  <Link href="/terms" className="hover:text-foreground">Terms of Service</Link>
                  <Link href="/security" className="hover:text-foreground">Security</Link>
                  <Link href="/dpa" className="hover:text-foreground">Data Processing</Link>
                </div>
              </div>
            </div>
            
            <div className="border-t border-divider/50 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="text-sm text-foreground/60">
                © 2025 AI Bookkeeper. All rights reserved.
              </div>
              <div className="flex gap-4">
                <Link
                  href="https://github.com/ContrejfC/ai-bookkeeper"
                  target="_blank"
                  className="text-foreground/60 hover:text-foreground text-sm"
                >
                  GitHub
                </Link>
                <Link
                  href="https://ai-bookkeeper-api-ww4vg3u7eq-uc.a.run.app/docs"
                  target="_blank"
                  className="text-foreground/60 hover:text-foreground text-sm"
                >
                  API Docs
                </Link>
                <Link
                  href="/pricing"
                  className="text-foreground/60 hover:text-foreground text-sm"
                >
                  Pricing
                </Link>
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
