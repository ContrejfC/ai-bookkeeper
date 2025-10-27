"use client";

import { motion } from "framer-motion";

export default function FlowingBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Animated SVG Pattern */}
      <motion.svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1200 800"
        preserveAspectRatio="none"
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
      
      {/* Floating Particles */}
      {[...Array(30)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-emerald-500/20 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [-30, 30, -30],
            x: [-10, 10, -10],
            opacity: [0.1, 0.6, 0.1],
            scale: [0.3, 1.2, 0.3],
          }}
          transition={{
            duration: 8 + Math.random() * 12,
            repeat: Infinity,
            ease: "easeInOut",
            delay: Math.random() * 5,
          }}
        />
      ))}
      
      {/* Additional Slow-Moving Particles */}
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={`slow-${i}`}
          className="absolute w-0.5 h-0.5 bg-cyan-500/15 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [-50, 50, -50],
            x: [-20, 20, -20],
            opacity: [0.05, 0.3, 0.05],
            scale: [0.2, 0.8, 0.2],
          }}
          transition={{
            duration: 20 + Math.random() * 20,
            repeat: Infinity,
            ease: "easeInOut",
            delay: Math.random() * 10,
          }}
        />
      ))}
    </div>
  );
}
