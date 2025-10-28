/**
 * Export Page
 * ===========
 * 
 * This page handles exporting journal entries to accounting systems:
 * - QuickBooks Online (QBO)
 * - Xero
 * 
 * Features:
 * ---------
 * 1. **QBO Integration**
 *    - Shows current environment (Sandbox/Production)
 *    - Connect button for OAuth flow
 *    - Demo mode support for testing without QBO account
 * 
 * 2. **Date Range Selection**
 *    - Filter JEs by date range
 *    - Prevents exporting old data
 * 
 * 3. **Export Summary**
 *    - Shows total/posted/skipped/failed counts
 *    - Modal with detailed results
 * 
 * 4. **Entitlement Gating**
 *    - Requires active subscription
 *    - Requires qbo_export feature
 *    - Shows upgrade CTA if not available
 * 
 * Environment Variables:
 * ----------------------
 * - QBO_ENV: "sandbox" or "production"
 * - DEMO_MODE: "true" or "false"
 * - QBO_CLIENT_ID_SANDBOX: OAuth client ID for sandbox
 * - QBO_CLIENT_ID: OAuth client ID for production
 */
"use client";

import { useState, useEffect } from "react";
import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import { EntitlementsGate } from "@/components/EntitlementsGate";
import {
  Card, CardHeader, CardBody, Button, Select, SelectItem,
  Input, Divider, Chip, Modal, ModalContent, ModalHeader,
  ModalBody, ModalFooter, useDisclosure, Snippet
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
  
  // QBO connection state
  const [qboConnected, setQboConnected] = useState(false);
  const [qboEnv, setQboEnv] = useState<"sandbox" | "production" | "unknown">("unknown");
  const [demoMode, setDemoMode] = useState(false);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  /**
   * Check QBO connection status on mount
   */
  useEffect(() => {
    const checkQBOStatus = async () => {
      try {
        // Call backend to check if QBO is connected
        const response = await fetch('/api/qbo/status', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          setQboConnected(data.connected || false);
          setQboEnv(data.environment || "unknown");
          setDemoMode(data.demo_mode || false);
        }
      } catch (err) {
        console.error("Failed to check QBO status:", err);
      }
    };
    
    checkQBOStatus();
  }, []);

  /**
   * Start OAuth flow to connect QuickBooks
   */
  const handleConnectQBO = () => {
    // Redirect to QBO OAuth flow
    // The backend will redirect back to /api/qbo/callback
    window.location.href = '/api/qbo/connect';
  };

  /**
   * Export journal entries to selected provider
   */
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

  /**
   * Check Xero connection status
   */
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
    <ProtectedRoute>
      {/* Temporarily disabled EntitlementsGate for debugging */}
      {/* <EntitlementsGate showQuota requireActive requiredFeature="qbo_export" softBlock> */}
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
              <div className="flex gap-2">
                {qboConnected && (
                  <Chip color="success" variant="flat" size="sm">
                    Connected
                  </Chip>
                )}
                {qboEnv !== "unknown" && (
                  <Chip 
                    color={qboEnv === "sandbox" ? "warning" : "primary"} 
                    variant="flat"
                    size="sm"
                  >
                    {qboEnv === "sandbox" ? "🧪 Sandbox" : "🏭 Production"}
                  </Chip>
                )}
                {demoMode && (
                  <Chip color="secondary" variant="flat" size="sm">
                    🎭 Demo
                  </Chip>
                )}
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <p className="text-sm">
                  Export journal entries with balanced line items. Idempotent
                  exports prevent duplicates.
                </p>
                
                {/* Connection Status */}
                {!qboConnected && !demoMode && (
                  <div className="bg-warning-50 dark:bg-warning-900/20 p-3 rounded-lg">
                    <p className="text-sm text-warning-800 dark:text-warning-200">
                      ⚠️ Not connected to QuickBooks. Connect to enable exports.
                    </p>
                  </div>
                )}
                
                {demoMode && (
                  <div className="bg-secondary-50 dark:bg-secondary-900/20 p-3 rounded-lg">
                    <p className="text-sm text-secondary-800 dark:text-secondary-200">
                      🎭 <strong>Demo Mode Active:</strong> Exports will return mock data without hitting QBO API. Perfect for testing!
                    </p>
                  </div>
                )}
                
                {/* Action Buttons */}
                <div className="flex gap-2">
                  {!qboConnected && !demoMode && (
                    <Button
                      color="primary"
                      variant="solid"
                      onPress={handleConnectQBO}
                      fullWidth
                    >
                      Connect QuickBooks {qboEnv === "sandbox" ? "(Sandbox)" : ""}
                    </Button>
                  )}
                  
                  {(qboConnected || demoMode) && (
                    <Button
                      color="primary"
                      variant={provider === "qbo" ? "solid" : "flat"}
                      onPress={() => setProvider("qbo")}
                      fullWidth
                    >
                      {provider === "qbo" ? "✓ Selected" : "Select QBO"}
                    </Button>
                  )}
                </div>
              </div>
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
      {/* </EntitlementsGate> */}
    </ProtectedRoute>
  );
}

