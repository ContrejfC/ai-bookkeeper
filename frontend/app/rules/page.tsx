"use client";

import { useState, useEffect } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Tabs, Tab, Table, TableHeader,
  TableColumn, TableBody, TableRow, TableCell, Button, Chip,
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter,
  useDisclosure, Divider
} from "@nextui-org/react";
import { rulesAPI } from "@/lib/api";

interface Candidate {
  id: string;
  vendor_pattern: string;
  suggested_account: string;
  evidence: {
    count: number;
    precision: number;
    std_dev: number;
  };
  status: "pending" | "accepted" | "rejected";
  created_at: string;
}

interface DryRunResult {
  before: {
    automation_rate: number;
    not_auto_post_counts: Record<string, number>;
  };
  after: {
    automation_rate: number;
    not_auto_post_counts: Record<string, number>;
  };
  affected_txn_ids: string[];
  deltas: Record<string, number>;
}

interface Version {
  version_id: string;
  created_by: string;
  created_at: string;
  is_active: boolean;
}

export default function RulesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set());
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);
  const [activeTab, setActiveTab] = useState("pending");
  
  const dryRunModal = useDisclosure();
  const versionsModal = useDisclosure();

  useEffect(() => {
    loadCandidates(activeTab);
  }, [activeTab]);

  const loadCandidates = async (status: string) => {
    try {
      const data = await rulesAPI.getCandidates(status === "all" ? undefined : status);
      setCandidates(data || []);
    } catch (err) {
      console.error("Failed to load candidates:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async () => {
    try {
      const data = await rulesAPI.getVersions();
      setVersions(data || []);
      versionsModal.onOpen();
    } catch (err) {
      console.error("Failed to load versions:", err);
    }
  };

  const handleDryRun = async () => {
    if (selectedCandidates.size === 0) return;

    try {
      const result = await rulesAPI.dryRun(
        Array.from(selectedCandidates),
        "demo-tenant" // TODO: Get from user context
      );
      setDryRunResult(result);
      dryRunModal.onOpen();
    } catch (err) {
      console.error("Dry run failed:", err);
      alert("Dry run failed. Please try again.");
    }
  };

  const handleAccept = async (id: string) => {
    try {
      await rulesAPI.accept(id);
      await loadCandidates(activeTab);
      setSelectedCandidates(new Set());
      alert("Rule candidate accepted successfully!");
    } catch (err: any) {
      console.error("Accept failed:", err);
      alert(err.data?.detail || "Failed to accept candidate.");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await rulesAPI.reject(id);
      await loadCandidates(activeTab);
      setSelectedCandidates(new Set());
      alert("Rule candidate rejected.");
    } catch (err) {
      console.error("Reject failed:", err);
      alert("Failed to reject candidate.");
    }
  };

  const handleRollback = async (versionId: string) => {
    try {
      await rulesAPI.rollback(versionId);
      await loadVersions();
      alert("Rollback successful!");
    } catch (err) {
      console.error("Rollback failed:", err);
      alert("Failed to rollback.");
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Rules Console</h1>
            <p className="text-sm opacity-60 mt-1">
              Review and manage automation rule candidates
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="flat" onPress={loadVersions}>
              View History
            </Button>
            <Button
              color="primary"
              onPress={handleDryRun}
              isDisabled={selectedCandidates.size === 0}
            >
              Dry Run ({selectedCandidates.size})
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <Tabs
              selectedKey={activeTab}
              onSelectionChange={(key) => setActiveTab(key as string)}
            >
              <Tab key="pending" title="Pending" />
              <Tab key="accepted" title="Accepted" />
              <Tab key="rejected" title="Rejected" />
            </Tabs>
          </CardHeader>
          <CardBody>
            <Table
              aria-label="Rule candidates"
              selectionMode={activeTab === "pending" ? "multiple" : "none"}
              selectedKeys={selectedCandidates}
              onSelectionChange={(keys) => setSelectedCandidates(new Set(keys as Set<string>))}
            >
              <TableHeader>
                <TableColumn>Vendor Pattern</TableColumn>
                <TableColumn>Suggested Account</TableColumn>
                <TableColumn>Evidence</TableColumn>
                <TableColumn>Status</TableColumn>
                <TableColumn>Actions</TableColumn>
              </TableHeader>
              <TableBody
                isLoading={loading}
                emptyContent="No candidates found"
              >
                {candidates.map((candidate) => (
                  <TableRow key={candidate.id}>
                    <TableCell className="font-mono text-sm">
                      {candidate.vendor_pattern}
                    </TableCell>
                    <TableCell>{candidate.suggested_account}</TableCell>
                    <TableCell>
                      <div className="text-xs">
                        <div>Count: {candidate.evidence.count}</div>
                        <div>
                          Precision: {(candidate.evidence.precision * 100).toFixed(1)}%
                        </div>
                        <div>Std Dev: {candidate.evidence.std_dev.toFixed(3)}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="sm"
                        color={
                          candidate.status === "accepted"
                            ? "success"
                            : candidate.status === "rejected"
                            ? "danger"
                            : "warning"
                        }
                      >
                        {candidate.status}
                      </Chip>
                    </TableCell>
                    <TableCell>
                      {candidate.status === "pending" && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            color="success"
                            variant="flat"
                            onPress={() => handleAccept(candidate.id)}
                          >
                            Accept
                          </Button>
                          <Button
                            size="sm"
                            color="danger"
                            variant="flat"
                            onPress={() => handleReject(candidate.id)}
                          >
                            Reject
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>

        {/* Dry Run Results Modal */}
        <Modal
          isOpen={dryRunModal.isOpen}
          onClose={dryRunModal.onClose}
          size="2xl"
        >
          <ModalContent>
            <ModalHeader>Dry Run Results</ModalHeader>
            <ModalBody>
              {dryRunResult && (
                <div className="flex flex-col gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="text-sm font-semibold">Before</CardHeader>
                      <CardBody>
                        <div className="text-2xl font-bold">
                          {(dryRunResult.before.automation_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs opacity-60">Automation Rate</div>
                      </CardBody>
                    </Card>
                    <Card>
                      <CardHeader className="text-sm font-semibold">After</CardHeader>
                      <CardBody>
                        <div className="text-2xl font-bold text-success">
                          {(dryRunResult.after.automation_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs opacity-60">
                          +{(dryRunResult.deltas.automation_rate * 100).toFixed(1)}%
                        </div>
                      </CardBody>
                    </Card>
                  </div>

                  <Divider />

                  <div>
                    <p className="text-sm font-semibold mb-2">Impact</p>
                    <div className="text-sm space-y-1">
                      <div>
                        Affected transactions:{" "}
                        <strong>{dryRunResult.affected_txn_ids.length}</strong>
                      </div>
                      <div>
                        Below threshold change:{" "}
                        <strong className="text-success">
                          {dryRunResult.deltas.below_threshold}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="bg-default-100 p-3 rounded text-xs opacity-60">
                    <strong>Note:</strong> This is a read-only simulation. No changes
                    have been made to the database.
                  </div>
                </div>
              )}
            </ModalBody>
            <ModalFooter>
              <Button onPress={dryRunModal.onClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Version History Modal */}
        <Modal
          isOpen={versionsModal.isOpen}
          onClose={versionsModal.onClose}
          size="2xl"
        >
          <ModalContent>
            <ModalHeader>Rule Version History</ModalHeader>
            <ModalBody>
              <Table aria-label="Version history">
                <TableHeader>
                  <TableColumn>Version ID</TableColumn>
                  <TableColumn>Created By</TableColumn>
                  <TableColumn>Created At</TableColumn>
                  <TableColumn>Status</TableColumn>
                  <TableColumn>Actions</TableColumn>
                </TableHeader>
                <TableBody emptyContent="No versions found">
                  {versions.map((version) => (
                    <TableRow key={version.version_id}>
                      <TableCell className="font-mono text-xs">
                        {version.version_id}
                      </TableCell>
                      <TableCell>{version.created_by}</TableCell>
                      <TableCell>
                        {new Date(version.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {version.is_active ? (
                          <Chip size="sm" color="success">
                            Active
                          </Chip>
                        ) : (
                          <Chip size="sm" variant="flat">
                            Inactive
                          </Chip>
                        )}
                      </TableCell>
                      <TableCell>
                        {!version.is_active && (
                          <Button
                            size="sm"
                            variant="flat"
                            onPress={() => handleRollback(version.version_id)}
                          >
                            Rollback
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ModalBody>
            <ModalFooter>
              <Button onPress={versionsModal.onClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    </AppShell>
  );
}

