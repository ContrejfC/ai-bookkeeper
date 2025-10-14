"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Select, SelectItem, Divider, Progress
} from "@nextui-org/react";

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("7d");

  // Sample data - replace with API call
  const metrics = {
    automation_rate: 0.87,
    transactions_processed: 342,
    auto_posted: 298,
    manual_review: 44,
    avg_confidence: 0.94,
    llm_usage_usd: 12.45,
    processing_time_avg_ms: 87,
  };

  const dailyStats = [
    { date: "2025-10-07", processed: 45, auto_posted: 39, confidence: 0.91 },
    { date: "2025-10-08", processed: 52, auto_posted: 47, confidence: 0.93 },
    { date: "2025-10-09", processed: 48, auto_posted: 41, confidence: 0.89 },
    { date: "2025-10-10", processed: 61, auto_posted: 54, confidence: 0.95 },
    { date: "2025-10-11", processed: 49, auto_posted: 43, confidence: 0.92 },
    { date: "2025-10-12", processed: 55, auto_posted: 48, confidence: 0.94 },
    { date: "2025-10-13", processed: 32, auto_posted: 26, confidence: 0.93 },
  ];

  const topVendors = [
    { name: "Amazon Web Services", count: 45, automation: 0.98 },
    { name: "Office Depot", count: 24, automation: 0.96 },
    { name: "Starbucks", count: 18, automation: 0.67 },
    { name: "Square", count: 15, automation: 0.93 },
    { name: "Google Workspace", count: 12, automation: 1.0 },
  ];

  const notAutoPostReasons = [
    { reason: "Below Threshold", count: 27, percentage: 61.4 },
    { reason: "Cold Start", count: 15, percentage: 34.1 },
    { reason: "Ambiguous", count: 2, percentage: 4.5 },
  ];

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-sm opacity-60 mt-1">
              System performance and automation metrics
            </p>
          </div>
          <Select
            size="sm"
            label="Time Range"
            selectedKeys={[timeRange]}
            onChange={(e) => setTimeRange(e.target.value)}
            className="w-40"
          >
            <SelectItem key="7d" value="7d">
              Last 7 days
            </SelectItem>
            <SelectItem key="30d" value="30d">
              Last 30 days
            </SelectItem>
            <SelectItem key="90d" value="90d">
              Last 90 days
            </SelectItem>
          </Select>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardHeader className="text-sm opacity-60">Automation Rate</CardHeader>
            <CardBody>
              <div className="text-2xl font-semibold text-success">
                {(metrics.automation_rate * 100).toFixed(1)}%
              </div>
              <Progress
                value={metrics.automation_rate * 100}
                color="success"
                size="sm"
                className="mt-2"
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="text-sm opacity-60">Transactions</CardHeader>
            <CardBody>
              <div className="text-2xl font-semibold">{metrics.transactions_processed}</div>
              <div className="text-xs opacity-60 mt-1">
                {metrics.auto_posted} auto-posted, {metrics.manual_review} manual
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="text-sm opacity-60">Avg Confidence</CardHeader>
            <CardBody>
              <div className="text-2xl font-semibold">
                {(metrics.avg_confidence * 100).toFixed(1)}%
              </div>
              <Progress
                value={metrics.avg_confidence * 100}
                color="primary"
                size="sm"
                className="mt-2"
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="text-sm opacity-60">LLM Usage</CardHeader>
            <CardBody>
              <div className="text-2xl font-semibold">
                ${metrics.llm_usage_usd.toFixed(2)}
              </div>
              <div className="text-xs opacity-60 mt-1">This period</div>
            </CardBody>
          </Card>
        </div>

        {/* Daily Trend */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Daily Activity</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {dailyStats.map((day) => (
                <div key={day.date} className="flex items-center gap-4">
                  <div className="text-xs opacity-60 w-24">{day.date}</div>
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span>
                        {day.auto_posted}/{day.processed} auto-posted
                      </span>
                      <span className="opacity-60">
                        {((day.auto_posted / day.processed) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Progress
                      value={(day.auto_posted / day.processed) * 100}
                      color="success"
                      size="sm"
                    />
                  </div>
                  <div className="text-xs opacity-60 w-20 text-right">
                    ⚡ {(day.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          {/* Top Vendors */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Top Vendors by Volume</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                {topVendors.map((vendor, idx) => (
                  <div key={vendor.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium">{vendor.name}</span>
                      <span className="opacity-60">{vendor.count} txns</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress
                        value={vendor.automation * 100}
                        color={vendor.automation > 0.9 ? "success" : "warning"}
                        size="sm"
                        className="flex-1"
                      />
                      <span className="text-xs opacity-60 w-12 text-right">
                        {(vendor.automation * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* Manual Review Reasons */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Manual Review Reasons</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                {notAutoPostReasons.map((item) => (
                  <div key={item.reason}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium">{item.reason}</span>
                      <span className="opacity-60">
                        {item.count} ({item.percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <Progress
                      value={item.percentage}
                      color="warning"
                      size="sm"
                    />
                  </div>
                ))}
              </div>
              <Divider className="my-4" />
              <div className="text-xs opacity-60">
                <p>
                  <strong>Below Threshold:</strong> Confidence below auto-post
                  threshold
                </p>
                <p className="mt-1">
                  <strong>Cold Start:</strong> New vendor with insufficient history
                </p>
                <p className="mt-1">
                  <strong>Ambiguous:</strong> Multiple possible accounts detected
                </p>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Performance Metrics */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">System Performance</h3>
          </CardHeader>
          <CardBody>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <div className="text-sm opacity-60">Avg Processing Time</div>
                <div className="text-xl font-semibold mt-1">
                  {metrics.processing_time_avg_ms}ms
                </div>
              </div>
              <div>
                <div className="text-sm opacity-60">Cache Hit Rate</div>
                <div className="text-xl font-semibold mt-1">97.8%</div>
              </div>
              <div>
                <div className="text-sm opacity-60">p95 Latency</div>
                <div className="text-xl font-semibold mt-1">245ms</div>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </AppShell>
  );
}

