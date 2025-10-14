"use client";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import { Card, CardHeader, CardBody } from "@nextui-org/react";
import { motion } from "framer-motion";
import { 
  TransactionIcon, 
  AnalyticsIcon, 
  VendorIcon, 
  ExportIcon 
} from "@/components/icons";

const Metric = ({ label, value, icon: Icon, delay = 0 }: {label: string; value: string; icon: any; delay?: number}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
  >
    <Card className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20 hover:border-emerald-400/40 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
      <CardHeader className="flex flex-row items-center justify-between">
        <span className="text-sm opacity-60">{label}</span>
        <div className="p-2 rounded-lg bg-gradient-to-r from-emerald-500/20 to-cyan-500/20">
          <Icon />
        </div>
      </CardHeader>
      <CardBody className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
        {value}
      </CardBody>
    </Card>
  </motion.div>
);

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <div className="space-y-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-slate-400 mt-2">Monitor your AI-powered bookkeeping automation</p>
          </motion.div>

          {/* Metrics Grid */}
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
            <Metric 
              label="Unposted Transactions" 
              value="47" 
              icon={TransactionIcon}
              delay={0.1}
            />
            <Metric 
              label="Reconciliation Rate" 
              value="92%" 
              icon={AnalyticsIcon}
              delay={0.2}
            />
            <Metric 
              label="Vendors with Rules" 
              value="21" 
              icon={VendorIcon}
              delay={0.3}
            />
            <Metric 
              label="Last Export" 
              value="Today 9:42a" 
              icon={ExportIcon}
              delay={0.4}
            />
          </div>

          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Card className="rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20">
              <CardHeader>
                <h2 className="text-xl font-semibold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  Recent Activity
                </h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <div>
                      <p className="font-medium">12 transactions reviewed today</p>
                      <p className="text-sm text-slate-400">All approved and posted</p>
                    </div>
                    <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse"></div>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                    <div>
                      <p className="font-medium">3 new vendor rules created</p>
                      <p className="text-sm text-slate-400">Automation rate improved</p>
                    </div>
                    <div className="w-3 h-3 bg-cyan-400 rounded-full"></div>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-teal-500/10 border border-teal-500/20">
                    <div>
                      <p className="font-medium">Weekly access snapshot completed</p>
                      <p className="text-sm text-slate-400">Compliance status: PASS</p>
                    </div>
                    <div className="w-3 h-3 bg-teal-400 rounded-full"></div>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div>
                      <p className="font-medium">Backup verification completed</p>
                      <p className="text-sm text-slate-400">Status: PASS</p>
                    </div>
                    <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  </div>
                </div>
              </CardBody>
            </Card>
          </motion.div>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}

