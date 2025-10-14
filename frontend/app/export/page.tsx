"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Button, Select, SelectItem,
  Input, Divider, Chip, Modal, ModalContent, ModalHeader,
  ModalBody, ModalFooter, useDisclosure
} from "@nextui-org/react";
import { exportAPI } from "@/lib/api";

interface ExportResult {
  tenant_id: string;
  summary: {
    total: number;
    posted: number;
    skipped: number;
    failed: number;
  };
}

export default function ExportPage() {
  const [tenantId, setTenantId] = useState("demo-tenant");
  const [dateFrom, setDateFrom] = useState("2024-10-01");
  const [dateTo, setDateTo] = useState("2024-10-31");
  const [provider, setProvider] = useState<"qbo" | "xero">("qbo");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExportResult | null>(null);
  
  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleExport = async () => {
    setLoading(true);
    try {
      const exportFn = provider === "qbo" ? exportAPI.toQBO : exportAPI.toXero;
      const data = await exportFn(tenantId, dateFrom, dateTo);
      setResult(data);
      onOpen();
    } catch (err: any) {
      console.error("Export failed:", err);
      alert(err.data?.detail || "Export failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckXeroStatus = async () => {
    try {
      const data = await exportAPI.getXeroStatus(tenantId);
      alert(JSON.stringify(data, null, 2));
    } catch (err) {
      console.error("Failed to get Xero status:", err);
      alert("Failed to get Xero status.");
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-3xl font-bold">Export to Accounting Systems</h1>
          <p className="text-sm opacity-60 mt-1">
            Export journal entries to QuickBooks Online or Xero
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* QuickBooks Online Card */}
          <Card className={provider === "qbo" ? "border-2 border-primary" : ""}>
            <CardHeader className="flex justify-between">
              <div>
                <h3 className="text-lg font-semibold">QuickBooks Online</h3>
                <p className="text-xs opacity-60 mt-1">Export to QBO via API</p>
              </div>
              <Chip color="success" variant="flat">
                Enabled
              </Chip>
            </CardHeader>
            <CardBody>
              <p className="text-sm mb-4">
                Export journal entries with balanced line items. Idempotent
                exports prevent duplicates.
              </p>
              <Button
                color="primary"
                variant={provider === "qbo" ? "solid" : "flat"}
                onPress={() => setProvider("qbo")}
                fullWidth
              >
                {provider === "qbo" ? "✓ Selected" : "Select QBO"}
              </Button>
            </CardBody>
          </Card>

          {/* Xero Card */}
          <Card className={provider === "xero" ? "border-2 border-primary" : ""}>
            <CardHeader className="flex justify-between">
              <div>
                <h3 className="text-lg font-semibold">Xero</h3>
                <p className="text-xs opacity-60 mt-1">Export to Xero via API</p>
              </div>
              <Chip color="success" variant="flat">
                Enabled
              </Chip>
            </CardHeader>
            <CardBody>
              <p className="text-sm mb-4">
                Export to Xero with manual journals. Supports account mapping and
                idempotent exports.
              </p>
              <Button
                color="primary"
                variant={provider === "xero" ? "solid" : "flat"}
                onPress={() => setProvider("xero")}
                fullWidth
              >
                {provider === "xero" ? "✓ Selected" : "Select Xero"}
              </Button>
              <Button
                size="sm"
                variant="light"
                onPress={handleCheckXeroStatus}
                className="mt-2"
                fullWidth
              >
                Check Xero Status
              </Button>
            </CardBody>
          </Card>
        </div>

        {/* Export Configuration */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Export Configuration</h3>
          </CardHeader>
          <CardBody>
            <div className="flex flex-col gap-4">
              <Input
                label="Tenant ID"
                value={tenantId}
                onValueChange={setTenantId}
                description="The tenant to export journal entries for"
              />

              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Date From"
                  type="date"
                  value={dateFrom}
                  onValueChange={setDateFrom}
                />
                <Input
                  label="Date To"
                  type="date"
                  value={dateTo}
                  onValueChange={setDateTo}
                />
              </div>

              <Divider />

              <div className="bg-default-100 p-4 rounded text-sm">
                <p className="font-semibold mb-2">Selected Provider: {provider.toUpperCase()}</p>
                <ul className="list-disc list-inside space-y-1 opacity-80">
                  <li>Export period: {dateFrom} to {dateTo}</li>
                  <li>Idempotent: Duplicate entries will be skipped</li>
                  <li>Balanced totals enforced automatically</li>
                  <li>All exports are logged in the audit trail</li>
                </ul>
              </div>

              <Button
                color="primary"
                size="lg"
                onPress={handleExport}
                isLoading={loading}
                startContent={
                  !loading && (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  )
                }
              >
                Export to {provider.toUpperCase()}
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Export History */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Recent Exports</h3>
          </CardHeader>
          <CardBody>
            <div className="text-sm opacity-60">
              <p>Export history will be displayed here in a future update.</p>
              <p className="mt-2">
                Check the Audit Log for detailed export records.
              </p>
            </div>
          </CardBody>
        </Card>

        {/* Export Results Modal */}
        <Modal isOpen={isOpen} onClose={onClose} size="lg">
          <ModalContent>
            <ModalHeader>Export Complete</ModalHeader>
            <ModalBody>
              {result && (
                <div className="flex flex-col gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardBody>
                        <div className="text-2xl font-bold text-success">
                          {result.summary.posted}
                        </div>
                        <div className="text-xs opacity-60">Posted</div>
                      </CardBody>
                    </Card>
                    <Card>
                      <CardBody>
                        <div className="text-2xl font-bold">
                          {result.summary.skipped}
                        </div>
                        <div className="text-xs opacity-60">Skipped (duplicates)</div>
                      </CardBody>
                    </Card>
                  </div>

                  <Divider />

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Total journal entries:</span>
                      <strong>{result.summary.total}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Successfully posted:</span>
                      <strong className="text-success">{result.summary.posted}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Skipped (already exist):</span>
                      <strong>{result.summary.skipped}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Failed:</span>
                      <strong className={result.summary.failed > 0 ? "text-danger" : ""}>
                        {result.summary.failed}
                      </strong>
                    </div>
                  </div>

                  <div className="bg-default-100 p-3 rounded text-xs opacity-80">
                    All exports are logged in the audit trail. Check the Audit page
                    for detailed information about each exported entry.
                  </div>
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              <Button onPress={onClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    </AppShell>
  );
}

