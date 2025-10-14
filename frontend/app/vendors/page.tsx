"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Table, TableHeader, TableColumn,
  TableBody, TableRow, TableCell, Input, Chip, Button, Progress
} from "@nextui-org/react";

interface Vendor {
  id: string;
  name: string;
  normalized_name: string;
  transaction_count: number;
  automation_rate: number;
  suggested_account: string;
  last_seen: string;
  has_rule: boolean;
}

// Sample data - replace with API call
const SAMPLE_VENDORS: Vendor[] = [
  {
    id: "v1",
    name: "Amazon Web Services",
    normalized_name: "amazon web services*",
    transaction_count: 45,
    automation_rate: 0.98,
    suggested_account: "Cloud Services",
    last_seen: "2025-10-13",
    has_rule: true,
  },
  {
    id: "v2",
    name: "Office Depot",
    normalized_name: "office depot*",
    transaction_count: 24,
    automation_rate: 0.96,
    suggested_account: "Office Supplies",
    last_seen: "2025-10-12",
    has_rule: true,
  },
  {
    id: "v3",
    name: "Starbucks",
    normalized_name: "starbucks*",
    transaction_count: 18,
    automation_rate: 0.67,
    suggested_account: "Meals & Entertainment",
    last_seen: "2025-10-11",
    has_rule: false,
  },
  {
    id: "v4",
    name: "Acme Corp",
    normalized_name: "acme corp*",
    transaction_count: 12,
    automation_rate: 1.0,
    suggested_account: "Revenue",
    last_seen: "2025-10-10",
    has_rule: true,
  },
  {
    id: "v5",
    name: "Local Coffee Shop",
    normalized_name: "local coffee shop*",
    transaction_count: 8,
    automation_rate: 0.25,
    suggested_account: "Meals & Entertainment",
    last_seen: "2025-10-09",
    has_rule: false,
  },
];

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>(SAMPLE_VENDORS);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredVendors = vendors.filter(
    (v) =>
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.normalized_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = {
    total: vendors.length,
    withRules: vendors.filter((v) => v.has_rule).length,
    avgAutomation:
      vendors.reduce((acc, v) => acc + v.automation_rate, 0) / vendors.length,
  };

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Vendors</h1>
          <p className="text-sm opacity-60 mt-1">
            Vendor patterns and automation rules
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="text-sm opacity-60">Total Vendors</CardHeader>
            <CardBody className="text-2xl font-semibold">{stats.total}</CardBody>
          </Card>
          <Card>
            <CardHeader className="text-sm opacity-60">With Rules</CardHeader>
            <CardBody className="text-2xl font-semibold">
              {stats.withRules}
              <span className="text-sm font-normal opacity-60 ml-2">
                ({((stats.withRules / stats.total) * 100).toFixed(0)}%)
              </span>
            </CardBody>
          </Card>
          <Card>
            <CardHeader className="text-sm opacity-60">Avg Automation</CardHeader>
            <CardBody className="text-2xl font-semibold">
              {(stats.avgAutomation * 100).toFixed(1)}%
            </CardBody>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-center w-full">
              <h3 className="text-lg font-semibold">All Vendors</h3>
              <Input
                size="sm"
                placeholder="Search vendors..."
                value={searchQuery}
                onValueChange={setSearchQuery}
                className="w-64"
              />
            </div>
          </CardHeader>
          <CardBody>
            <Table aria-label="Vendors">
              <TableHeader>
                <TableColumn>Vendor Name</TableColumn>
                <TableColumn>Normalized Pattern</TableColumn>
                <TableColumn>Transactions</TableColumn>
                <TableColumn>Automation Rate</TableColumn>
                <TableColumn>Suggested Account</TableColumn>
                <TableColumn>Rule Status</TableColumn>
                <TableColumn>Last Seen</TableColumn>
              </TableHeader>
              <TableBody emptyContent="No vendors found">
                {filteredVendors.map((vendor) => (
                  <TableRow key={vendor.id}>
                    <TableCell className="font-semibold">{vendor.name}</TableCell>
                    <TableCell className="font-mono text-xs opacity-70">
                      {vendor.normalized_name}
                    </TableCell>
                    <TableCell>{vendor.transaction_count}</TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <Progress
                          size="sm"
                          value={vendor.automation_rate * 100}
                          color={
                            vendor.automation_rate > 0.9
                              ? "success"
                              : vendor.automation_rate > 0.7
                              ? "warning"
                              : "danger"
                          }
                        />
                        <span className="text-xs">
                          {(vendor.automation_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{vendor.suggested_account}</TableCell>
                    <TableCell>
                      <Chip
                        size="sm"
                        color={vendor.has_rule ? "success" : "default"}
                        variant="flat"
                      >
                        {vendor.has_rule ? "Has Rule" : "No Rule"}
                      </Chip>
                    </TableCell>
                    <TableCell className="text-xs opacity-70">
                      {vendor.last_seen}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>

        <div className="bg-default-100 p-4 rounded text-sm opacity-80">
          <p className="font-semibold mb-2">About Vendor Patterns</p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              Normalized patterns use wildcards (*) to match similar vendor names
            </li>
            <li>
              Automation rate shows what percentage of transactions are auto-posted
            </li>
            <li>
              Vendors with high transaction counts are good candidates for rules
            </li>
            <li>Check the Rules Console to create or modify vendor rules</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}

