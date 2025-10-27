"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import { EntitlementsGate } from "@/components/EntitlementsGate";
import {
  Card, CardHeader, CardBody, Button, Input, Select, SelectItem,
  Divider
} from "@nextui-org/react";
import { auditAPI } from "@/lib/api";

export default function AuditPage() {
  const [filters, setFilters] = useState({
    tenant_id: "",
    vendor: "",
    action: "",
    reason: "",
    user_id: "",
    start_ts: "",
    end_ts: "",
  });

  const handleDownloadCSV = () => {
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([_, value]) => value !== "")
    );
    
    const url = auditAPI.exportCSV(cleanFilters);
    window.open(url, "_blank");
  };

  const handleReset = () => {
    setFilters({
      tenant_id: "",
      vendor: "",
      action: "",
      reason: "",
      user_id: "",
      start_ts: "",
      end_ts: "",
    });
  };

  return (
    <ProtectedRoute>
      <EntitlementsGate showQuota requireActive>
        <AppShell>
          <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Audit Log Export</h1>
          <p className="text-sm opacity-60 mt-1">
            Export audit logs with filters as CSV
          </p>
        </div>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Filters</h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label="Tenant ID"
                placeholder="e.g., pilot-acme-corp"
                value={filters.tenant_id}
                onValueChange={(val) =>
                  setFilters({ ...filters, tenant_id: val })
                }
              />

              <Input
                label="Vendor"
                placeholder="Partial match"
                value={filters.vendor}
                onValueChange={(val) =>
                  setFilters({ ...filters, vendor: val })
                }
              />

              <Select
                label="Action"
                placeholder="Select action"
                selectedKeys={filters.action ? [filters.action] : []}
                onChange={(e) =>
                  setFilters({ ...filters, action: e.target.value })
                }
              >
                <SelectItem key="auto_posted" value="auto_posted">
                  Auto Posted
                </SelectItem>
                <SelectItem key="manual_review" value="manual_review">
                  Manual Review
                </SelectItem>
                <SelectItem key="rejected" value="rejected">
                  Rejected
                </SelectItem>
                <SelectItem key="approved" value="approved">
                  Approved
                </SelectItem>
              </Select>

              <Select
                label="Not Auto-Post Reason"
                placeholder="Select reason"
                selectedKeys={filters.reason ? [filters.reason] : []}
                onChange={(e) =>
                  setFilters({ ...filters, reason: e.target.value })
                }
              >
                <SelectItem key="below_threshold" value="below_threshold">
                  Below Threshold
                </SelectItem>
                <SelectItem key="cold_start" value="cold_start">
                  Cold Start
                </SelectItem>
                <SelectItem key="ambiguous" value="ambiguous">
                  Ambiguous
                </SelectItem>
              </Select>

              <Input
                label="User ID"
                placeholder="e.g., user-admin-001"
                value={filters.user_id}
                onValueChange={(val) =>
                  setFilters({ ...filters, user_id: val })
                }
              />

              <Input
                label="Start Date (ISO)"
                type="datetime-local"
                value={filters.start_ts}
                onValueChange={(val) =>
                  setFilters({ ...filters, start_ts: val ? `${val}:00Z` : "" })
                }
                description="Format: YYYY-MM-DDTHH:mm"
              />

              <Input
                label="End Date (ISO)"
                type="datetime-local"
                value={filters.end_ts}
                onValueChange={(val) =>
                  setFilters({ ...filters, end_ts: val ? `${val}:00Z` : "" })
                }
                description="Format: YYYY-MM-DDTHH:mm"
              />
            </div>

            <Divider className="my-6" />

            <div className="flex gap-3">
              <Button
                color="primary"
                onPress={handleDownloadCSV}
                startContent={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
              >
                Download CSV
              </Button>
              <Button variant="flat" onPress={handleReset}>
                Reset Filters
              </Button>
            </div>

            <div className="mt-6 p-4 bg-default-100 rounded text-sm opacity-80">
              <p className="font-semibold mb-2">Export Information</p>
              <ul className="list-disc list-inside space-y-1">
                <li>CSV export is memory-bounded and supports 100k+ rows</li>
                <li>Timestamps are in UTC ISO8601 format</li>
                <li>All filters are optional and can be combined</li>
                <li>
                  CSV includes: timestamp, tenant_id, user_id, action, txn_id,
                  vendor, calibrated_p, threshold_used, not_auto_post_reason,
                  cold_start_label_count, ruleset_version_id, model_version_id
                </li>
              </ul>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Recent Exports</h3>
          </CardHeader>
          <CardBody>
            <div className="text-sm opacity-60">
              <p>Export history will be displayed here in a future update.</p>
              <p className="mt-2">
                For now, all exports download immediately as CSV files.
              </p>
            </div>
          </CardBody>
        </Card>
          </div>
        </AppShell>
      </EntitlementsGate>
    </ProtectedRoute>
  );
}

