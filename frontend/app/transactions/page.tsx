"use client";

import AppShell from "@/components/layout/AppShell";
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  Input, Select, SelectItem, Button, Modal, ModalContent, ModalHeader,
  ModalBody, ModalFooter, useDisclosure, Chip
} from "@nextui-org/react";
import { useMemo, useState } from "react";

type Txn = {
  id: string; date: string; payee: string; amount: number;
  status: "proposed" | "approved" | "posted"; account: string; category: string;
};

const SAMPLE: Txn[] = [
  { id:"t1", date:"2025-10-10", payee:"Stripe", amount: -129.99, status:"proposed", account:"Checking", category:"Fees" },
  { id:"t2", date:"2025-10-09", payee:"Amazon", amount: -59.25, status:"approved", account:"Card", category:"Office" },
  { id:"t3", date:"2025-10-08", payee:"Square", amount: 740.00, status:"proposed", account:"Checking", category:"Sales" },
  { id:"t4", date:"2025-10-07", payee:"Google Workspace", amount: -12.00, status:"posted", account:"Card", category:"Software" },
  { id:"t5", date:"2025-10-07", payee:"Acme Corp", amount: 1250.00, status:"proposed", account:"Checking", category:"Revenue" },
];

export default function TransactionsPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<"all"|"proposed"|"approved"|"posted">("all");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const approve = useDisclosure();
  
  const data = useMemo(() => {
    return SAMPLE.filter(t =>
      (status === "all" || t.status === status) &&
      (q === "" || t.payee.toLowerCase().includes(q.toLowerCase()))
    );
  }, [q, status]);

  const canApprove = selected.size > 0;
  const selectedTxns = SAMPLE.filter(t => selected.has(t.id));

  return (
    <AppShell>
      <div className="flex flex-col gap-4">
        <div>
          <h1 className="text-3xl font-bold">Transactions</h1>
          <p className="text-sm opacity-60 mt-1">Review and approve transactions</p>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <Input
            size="sm"
            placeholder="Search payee…"
            value={q}
            onValueChange={setQ}
            className="w-60"
          />
          <Select
            size="sm"
            selectedKeys={[status]}
            onChange={(e) => setStatus((e.target.value as any) || "all")}
            labelPlacement="outside-left"
            className="w-44"
            label="Status"
          >
            {["all","proposed","approved","posted"].map(s=>(
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </Select>
          <Button color="primary" size="sm" isDisabled={!canApprove} onPress={approve.onOpen}>
            Approve & Post ({selected.size})
          </Button>
        </div>

        <Table
          aria-label="Transactions"
          selectionMode="multiple"
          selectedKeys={selected}
          onSelectionChange={(keys)=> setSelected(new Set(keys as Set<string>))}
          className="rounded-2xl"
        >
          <TableHeader>
            <TableColumn>Date</TableColumn>
            <TableColumn>Payee</TableColumn>
            <TableColumn align="end">Amount</TableColumn>
            <TableColumn>Status</TableColumn>
            <TableColumn>Account</TableColumn>
            <TableColumn>Category</TableColumn>
          </TableHeader>
          <TableBody emptyContent={"No transactions"}>
            {data.map(t=>(
              <TableRow key={t.id}>
                <TableCell>{t.date}</TableCell>
                <TableCell>{t.payee}</TableCell>
                <TableCell className={t.amount < 0 ? "text-danger" : "text-success"}>
                  {t.amount.toLocaleString(undefined, { style: "currency", currency: "USD" })}
                </TableCell>
                <TableCell>
                  <Chip size="sm" color={t.status === "proposed" ? "warning" : t.status === "approved" ? "primary" : "success"}>
                    {t.status}
                  </Chip>
                </TableCell>
                <TableCell>{t.account}</TableCell>
                <TableCell>{t.category}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <Modal isOpen={approve.isOpen} onOpenChange={approve.onOpenChange} placement="center">
          <ModalContent>
            {(onClose)=>(
              <>
                <ModalHeader className="flex flex-col gap-1">Approve & Post</ModalHeader>
                <ModalBody>
                  <p className="mb-2">
                    <strong>{selected.size}</strong> transaction(s) will be approved and posted to the ledger:
                  </p>
                  <div className="flex flex-col gap-1 text-sm">
                    {selectedTxns.map(t => (
                      <div key={t.id} className="flex justify-between">
                        <span>{t.payee}</span>
                        <span className={t.amount < 0 ? "text-danger" : "text-success"}>
                          {t.amount.toLocaleString(undefined, { style: "currency", currency: "USD" })}
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs opacity-60 mt-2">
                    This is a dry-run stub. In production, this would call <code>/api/transactions/approve</code>.
                  </p>
                </ModalBody>
                <ModalFooter>
                  <Button variant="light" onPress={onClose}>Cancel</Button>
                  <Button color="primary" onPress={() => {
                    alert(`Would approve ${selected.size} transactions`);
                    setSelected(new Set());
                    onClose();
                  }}>
                    Confirm
                  </Button>
                </ModalFooter>
              </>
            )}
          </ModalContent>
        </Modal>
      </div>
    </AppShell>
  );
}

