"use client";

import { useState, useEffect } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Table, TableHeader, TableColumn,
  TableBody, TableRow, TableCell, Button, Modal, ModalContent,
  ModalHeader, ModalBody, ModalFooter, useDisclosure, Input,
  Switch, Chip
} from "@nextui-org/react";
import { tenantsAPI } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";

interface Tenant {
  tenant_id: string;
  name: string;
  autopost_enabled: boolean;
  autopost_threshold: number;
  llm_tenant_cap_usd: number;
  updated_at?: string;
}

export default function FirmPage() {
  const { user } = useAuth();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [formData, setFormData] = useState({
    autopost_enabled: false,
    autopost_threshold: 0.90,
    llm_tenant_cap_usd: 50.0,
  });

  const isOwner = user?.role === "owner";

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const data = await tenantsAPI.list();
      setTenants(data.tenants || []);
    } catch (err) {
      console.error("Failed to load tenants:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setFormData({
      autopost_enabled: tenant.autopost_enabled,
      autopost_threshold: tenant.autopost_threshold,
      llm_tenant_cap_usd: tenant.llm_tenant_cap_usd,
    });
    onOpen();
  };

  const handleSave = async () => {
    if (!selectedTenant) return;

    try {
      await tenantsAPI.updateSettings(selectedTenant.tenant_id, formData);
      await loadTenants();
      onClose();
    } catch (err) {
      console.error("Failed to update settings:", err);
      alert("Failed to update settings. Please try again.");
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Firm Settings</h1>
            <p className="text-sm opacity-60 mt-1">
              Manage tenant settings and automation thresholds
            </p>
          </div>
          {!isOwner && (
            <Chip color="primary" variant="flat">Staff View</Chip>
          )}
        </div>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">
              {isOwner ? "All Tenants" : "Assigned Tenants"}
            </h3>
          </CardHeader>
          <CardBody>
            <Table aria-label="Tenants">
              <TableHeader>
                <TableColumn>Tenant ID</TableColumn>
                <TableColumn>Name</TableColumn>
                <TableColumn>Auto-Post</TableColumn>
                <TableColumn>Threshold</TableColumn>
                <TableColumn>LLM Cap (USD)</TableColumn>
                <TableColumn>Actions</TableColumn>
              </TableHeader>
              <TableBody
                isLoading={loading}
                emptyContent="No tenants found"
              >
                {tenants.map((tenant) => (
                  <TableRow key={tenant.tenant_id}>
                    <TableCell className="font-mono text-xs">
                      {tenant.tenant_id}
                    </TableCell>
                    <TableCell>{tenant.name}</TableCell>
                    <TableCell>
                      <Chip
                        size="sm"
                        color={tenant.autopost_enabled ? "success" : "default"}
                        variant="flat"
                      >
                        {tenant.autopost_enabled ? "Enabled" : "Disabled"}
                      </Chip>
                    </TableCell>
                    <TableCell>
                      {(tenant.autopost_threshold * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell>${tenant.llm_tenant_cap_usd}</TableCell>
                    <TableCell>
                      {isOwner && (
                        <Button
                          size="sm"
                          variant="flat"
                          onPress={() => handleEdit(tenant)}
                        >
                          Edit
                        </Button>
                      )}
                      {!isOwner && (
                        <span className="text-xs opacity-60">View Only</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>

        <Modal isOpen={isOpen} onClose={onClose} size="lg">
          <ModalContent>
            <ModalHeader>
              Edit Settings: {selectedTenant?.name}
            </ModalHeader>
            <ModalBody>
              <div className="flex flex-col gap-4">
                <Switch
                  isSelected={formData.autopost_enabled}
                  onValueChange={(checked) =>
                    setFormData({ ...formData, autopost_enabled: checked })
                  }
                >
                  Enable Auto-Post
                </Switch>

                <Input
                  label="Auto-Post Threshold"
                  type="number"
                  min="0.80"
                  max="0.98"
                  step="0.01"
                  value={formData.autopost_threshold.toString()}
                  onValueChange={(val) =>
                    setFormData({ ...formData, autopost_threshold: parseFloat(val) })
                  }
                  description="Must be between 0.80 and 0.98"
                  endContent={
                    <span className="text-sm opacity-60">
                      {(formData.autopost_threshold * 100).toFixed(0)}%
                    </span>
                  }
                />

                <Input
                  label="LLM Monthly Cap (USD)"
                  type="number"
                  min="0"
                  step="10"
                  value={formData.llm_tenant_cap_usd.toString()}
                  onValueChange={(val) =>
                    setFormData({ ...formData, llm_tenant_cap_usd: parseFloat(val) })
                  }
                  startContent={<span>$</span>}
                />

                <div className="text-xs opacity-60 bg-default-100 p-3 rounded">
                  <p>
                    <strong>Note:</strong> Changes will be logged in the audit trail
                    and take effect immediately.
                  </p>
                </div>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onClose}>
                Cancel
              </Button>
              <Button color="primary" onPress={handleSave}>
                Save Changes
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    </AppShell>
  );
}

