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
    <Card className="rounded-xl sm:rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20 hover:border-emerald-400/40 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <span className="text-xs sm:text-sm opacity-60">{label}</span>
        <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-r from-emerald-500/20 to-cyan-500/20">
          <Icon />
        </div>
      </CardHeader>
      <CardBody className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent pt-0">
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
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-sm sm:text-base text-slate-400 mt-2">Monitor your AI-powered bookkeeping automation</p>
          </motion.div>

          {/* Metrics Grid */}
          <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
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
            <Card className="rounded-xl sm:rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20">
              <CardHeader>
                <h2 className="text-lg sm:text-xl font-semibold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  Recent Activity
                </h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-sm sm:text-base font-medium truncate">12 transactions reviewed today</p>
                      <p className="text-xs sm:text-sm text-slate-400">All approved and posted</p>
                    </div>
                    <div className="w-2 h-2 sm:w-3 sm:h-3 bg-emerald-400 rounded-full animate-pulse flex-shrink-0"></div>
                  </div>
                  <div className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-sm sm:text-base font-medium truncate">3 new vendor rules created</p>
                      <p className="text-xs sm:text-sm text-slate-400">Automation rate improved</p>
                    </div>
                    <div className="w-2 h-2 sm:w-3 sm:h-3 bg-cyan-400 rounded-full flex-shrink-0"></div>
                  </div>
                  <div className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-teal-500/10 border border-teal-500/20">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-sm sm:text-base font-medium truncate">Weekly access snapshot completed</p>
                      <p className="text-xs sm:text-sm text-slate-400">Compliance status: PASS</p>
                    </div>
                    <div className="w-2 h-2 sm:w-3 sm:h-3 bg-teal-400 rounded-full flex-shrink-0"></div>
                  </div>
                  <div className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-sm sm:text-base font-medium truncate">Backup verification completed</p>
                      <p className="text-xs sm:text-sm text-slate-400">Status: PASS</p>
                    </div>
                    <div className="w-2 h-2 sm:w-3 sm:h-3 bg-green-400 rounded-full flex-shrink-0"></div>
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

