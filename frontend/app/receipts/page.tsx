"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Card, CardHeader, CardBody, Button, Table, TableHeader,
  TableColumn, TableBody, TableRow, TableCell, Chip, Input
} from "@nextui-org/react";

interface ReceiptItem {
  id: string;
  filename: string;
  vendor: string;
  amount: string;
  date: string;
  status: "processed" | "pending" | "error";
  confidence: number;
  uploaded_at: string;
}

// Sample data - replace with API call
const SAMPLE_RECEIPTS: ReceiptItem[] = [
  {
    id: "rcpt-001",
    filename: "receipt_2024-10-13.jpg",
    vendor: "Office Depot",
    amount: "$125.99",
    date: "2024-10-13",
    status: "processed",
    confidence: 0.97,
    uploaded_at: "2024-10-13T10:30:00Z",
  },
  {
    id: "rcpt-002",
    filename: "receipt_2024-10-12.jpg",
    vendor: "Amazon",
    amount: "$59.25",
    date: "2024-10-12",
    status: "processed",
    confidence: 0.94,
    uploaded_at: "2024-10-12T15:20:00Z",
  },
  {
    id: "rcpt-003",
    filename: "receipt_2024-10-11.jpg",
    vendor: "Starbucks",
    amount: "$12.50",
    date: "2024-10-11",
    status: "processed",
    confidence: 0.89,
    uploaded_at: "2024-10-11T09:15:00Z",
  },
  {
    id: "rcpt-004",
    filename: "receipt_2024-10-10.jpg",
    vendor: "Gas Station",
    amount: "$45.00",
    date: "2024-10-10",
    status: "pending",
    confidence: 0.0,
    uploaded_at: "2024-10-10T16:45:00Z",
  },
];

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<ReceiptItem[]>(SAMPLE_RECEIPTS);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredReceipts = receipts.filter(
    (r) =>
      r.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.vendor.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleUpload = () => {
    alert("Upload functionality coming soon!");
  };

  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:gap-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold">Receipts</h1>
            <p className="text-xs sm:text-sm opacity-60 mt-1">
              View and manage receipt OCR processing
            </p>
          </div>
          <Button color="primary" onPress={handleUpload} size="sm" className="w-full sm:w-auto">
            Upload Receipt
          </Button>
        </div>

        <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-3">
          <Card className="rounded-xl sm:rounded-2xl">
            <CardHeader className="text-xs sm:text-sm opacity-60 pb-2">Total Receipts</CardHeader>
            <CardBody className="text-xl sm:text-2xl font-semibold pt-0">
              {receipts.length}
            </CardBody>
          </Card>
          <Card className="rounded-xl sm:rounded-2xl">
            <CardHeader className="text-xs sm:text-sm opacity-60 pb-2">Processed</CardHeader>
            <CardBody className="text-xl sm:text-2xl font-semibold pt-0">
              {receipts.filter((r) => r.status === "processed").length}
            </CardBody>
          </Card>
          <Card className="rounded-xl sm:rounded-2xl">
            <CardHeader className="text-xs sm:text-sm opacity-60 pb-2">Avg Confidence</CardHeader>
            <CardBody className="text-xl sm:text-2xl font-semibold pt-0">
              {(
                (receipts
                  .filter((r) => r.status === "processed")
                  .reduce((acc, r) => acc + r.confidence, 0) /
                  receipts.filter((r) => r.status === "processed").length) *
                100
              ).toFixed(1)}
              %
            </CardBody>
          </Card>
        </div>

        <Card className="rounded-xl sm:rounded-2xl">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 w-full">
              <h3 className="text-base sm:text-lg font-semibold">All Receipts</h3>
              <Input
                size="sm"
                placeholder="Search receipts..."
                value={searchQuery}
                onValueChange={setSearchQuery}
                className="w-full sm:w-64"
              />
            </div>
          </CardHeader>
          <CardBody className="overflow-x-auto -mx-3 sm:mx-0 px-3 sm:px-6">
            <div className="min-w-[640px] sm:min-w-0">
              <Table 
                aria-label="Receipts"
                classNames={{
                  wrapper: "p-0",
                  th: "text-xs sm:text-sm",
                  td: "text-xs sm:text-sm"
                }}
              >
                <TableHeader>
                  <TableColumn className="hidden md:table-cell">Filename</TableColumn>
                  <TableColumn>Vendor</TableColumn>
                  <TableColumn>Amount</TableColumn>
                  <TableColumn className="hidden sm:table-cell">Date</TableColumn>
                  <TableColumn>Status</TableColumn>
                  <TableColumn className="hidden lg:table-cell">Confidence</TableColumn>
                  <TableColumn className="hidden md:table-cell">Uploaded</TableColumn>
                  <TableColumn>Actions</TableColumn>
                </TableHeader>
                <TableBody emptyContent="No receipts found">
                  {filteredReceipts.map((receipt) => (
                    <TableRow key={receipt.id}>
                      <TableCell className="font-mono text-xs hidden md:table-cell">
                        {receipt.filename}
                      </TableCell>
                      <TableCell className="font-medium">{receipt.vendor}</TableCell>
                      <TableCell className="font-semibold whitespace-nowrap">{receipt.amount}</TableCell>
                      <TableCell className="hidden sm:table-cell whitespace-nowrap">{receipt.date}</TableCell>
                      <TableCell>
                        <Chip
                          size="sm"
                          color={
                            receipt.status === "processed"
                              ? "success"
                              : receipt.status === "pending"
                              ? "warning"
                              : "danger"
                          }
                        >
                          {receipt.status}
                        </Chip>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        {receipt.status === "processed" ? (
                          <Chip
                            size="sm"
                            variant="flat"
                            color={
                              receipt.confidence > 0.95
                                ? "success"
                                : receipt.confidence > 0.85
                                ? "warning"
                                : "danger"
                            }
                          >
                            {(receipt.confidence * 100).toFixed(0)}%
                          </Chip>
                        ) : (
                          <span className="text-xs opacity-60">N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs opacity-70 hidden md:table-cell">
                        {new Date(receipt.uploaded_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="flat"
                          href={`/receipts/${receipt.id}`}
                          as="a"
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardBody>
        </Card>

        <Card className="rounded-xl sm:rounded-2xl">
          <CardHeader>
            <h3 className="text-base sm:text-lg font-semibold">OCR Processing</h3>
          </CardHeader>
          <CardBody>
            <div className="text-xs sm:text-sm opacity-80 space-y-2">
              <p>
                Receipts are processed using <strong>Tesseract OCR</strong> with
                token-level bounding boxes for precise field extraction.
              </p>
              <p>
                <strong>Performance:</strong> ~500ms cold extraction, ~3ms cached
                retrieval (99.4% faster with caching).
              </p>
              <p>
                <strong>Accuracy:</strong> ≥90% IoU on field extraction with automatic
                fallback to heuristic methods if OCR is unavailable.
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </AppShell>
  );
}

