"use client";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell,
  Input, Select, SelectItem, Button, Modal, ModalContent, ModalHeader,
  ModalBody, ModalFooter, useDisclosure, Chip
} from "@nextui-org/react";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TransactionIcon } from "@/components/icons";

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
              Transactions
            </h1>
            <p className="text-sm sm:text-base text-slate-400 mt-2">Review and approve AI-categorized transactions</p>
          </motion.div>

          {/* Filters */}
          <motion.div 
            className="flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-4 items-stretch sm:items-center p-3 sm:p-4 rounded-xl sm:rounded-2xl bg-gradient-to-r from-slate-800/50 to-slate-900/50 border border-emerald-500/20"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="flex items-center gap-2 sm:hidden">
              <TransactionIcon />
              <span className="text-sm font-medium text-slate-300">Filters</span>
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <TransactionIcon />
              <span className="text-sm font-medium text-slate-300">Filters</span>
            </div>
            <Input
              size="sm"
              placeholder="Search payee…"
              value={q}
              onValueChange={setQ}
              className="w-full sm:w-60"
              classNames={{
                input: "bg-slate-800/50 border-emerald-500/20",
                inputWrapper: "bg-slate-800/50 border-emerald-500/20 hover:border-emerald-400/40"
              }}
            />
            <Select
              size="sm"
              selectedKeys={[status]}
              onChange={(e) => setStatus((e.target.value as any) || "all")}
              labelPlacement="outside-left"
              className="w-full sm:w-44"
              label="Status"
              classNames={{
                trigger: "bg-slate-800/50 border-emerald-500/20 hover:border-emerald-400/40",
                value: "text-slate-200"
              }}
            >
              {["all","proposed","approved","posted"].map(s=>(
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </Select>
            <Button 
              color="primary" 
              size="sm" 
              isDisabled={!canApprove} 
              onPress={approve.onOpen}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white disabled:opacity-50 w-full sm:w-auto"
            >
              Approve & Post ({selected.size})
            </Button>
          </motion.div>

          {/* Transactions Table */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="overflow-x-auto -mx-3 sm:mx-0"
          >
            <div className="min-w-[640px] sm:min-w-0">
              <Table
                aria-label="Transactions"
                selectionMode="multiple"
                selectedKeys={selected}
                onSelectionChange={(keys)=> setSelected(new Set(keys as Set<string>))}
                className="rounded-xl sm:rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-emerald-500/20"
                classNames={{
                  wrapper: "bg-slate-800/30 p-0",
                  thead: "bg-slate-900/50",
                  tbody: "bg-slate-800/30",
                  th: "text-xs sm:text-sm",
                  td: "text-xs sm:text-sm"
                }}
              >
            <TableHeader>
              <TableColumn>Date</TableColumn>
              <TableColumn>Payee</TableColumn>
              <TableColumn align="end">Amount</TableColumn>
              <TableColumn>Status</TableColumn>
              <TableColumn className="hidden sm:table-cell">Account</TableColumn>
              <TableColumn className="hidden sm:table-cell">Category</TableColumn>
            </TableHeader>
          <TableBody emptyContent={"No transactions"}>
            {data.map(t=>(
              <TableRow key={t.id}>
                <TableCell className="whitespace-nowrap">{t.date}</TableCell>
                <TableCell className="font-medium">{t.payee}</TableCell>
                <TableCell className={t.amount < 0 ? "text-red-400 font-semibold whitespace-nowrap" : "text-emerald-400 font-semibold whitespace-nowrap"}>
                  {t.amount.toLocaleString(undefined, { style: "currency", currency: "USD" })}
                </TableCell>
                <TableCell>
                  <Chip 
                    size="sm" 
                    className={
                      t.status === "proposed" 
                        ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" 
                        : t.status === "approved" 
                        ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                        : "bg-cyan-500/20 text-cyan-400 border-cyan-500/30"
                    }
                  >
                    {t.status}
                  </Chip>
                </TableCell>
                <TableCell className="hidden sm:table-cell">{t.account}</TableCell>
                <TableCell className="hidden sm:table-cell">{t.category}</TableCell>
              </TableRow>
            ))}
          </TableBody>
              </Table>
            </div>
          </motion.div>

          {/* Approve Modal */}
          <Modal 
            isOpen={approve.isOpen} 
            onOpenChange={approve.onOpenChange} 
            placement="center"
            classNames={{
              backdrop: "bg-black/80 backdrop-blur-sm",
              base: "bg-slate-900 border border-emerald-500/20",
              header: "border-b border-emerald-500/20",
              body: "bg-slate-800/50",
              footer: "border-t border-emerald-500/20"
            }}
          >
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
                  <Button 
                    variant="light" 
                    onPress={onClose}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    Cancel
                  </Button>
                  <Button 
                    className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white"
                    onPress={() => {
                      alert(`Would approve ${selected.size} transactions`);
                      setSelected(new Set());
                      onClose();
                    }}
                  >
                    Confirm Approval
                  </Button>
                </ModalFooter>
              </>
            )}
          </ModalContent>
        </Modal>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}

