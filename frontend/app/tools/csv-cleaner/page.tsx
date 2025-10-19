'use client';

import { useEffect, useState, useCallback } from 'react';
import { Button, Card, CardBody, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@nextui-org/react';
import { trackToolOpened, trackRowsPreviewed, trackExportPaywalled } from '@/lib/analytics';

interface PreviewRow {
  date: string;
  payee: string;
  memo: string;
  amount: number;
  suggested_account: string;
  confidence: number;
}

interface PreviewResponse {
  preview_rows: PreviewRow[];
  total_rows: number;
  message?: string;
}

export default function CSVCleanerPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';

  useEffect(() => {
    trackToolOpened('csv-cleaner');
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'text/csv') {
      if (droppedFile.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10 MB.');
        return;
      }
      setFile(droppedFile);
      uploadFile(droppedFile);
    } else {
      setError('Please upload a CSV file.');
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10 MB.');
        return;
      }
      setFile(selectedFile);
      uploadFile(selectedFile);
    }
  };

  const uploadFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setPreview(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/api/tools/csv-clean?preview=true`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data: PreviewResponse = await response.json();
      setPreview(data);
      trackRowsPreviewed(data.total_rows);
    } catch (err: any) {
      setError(err.message || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  const handlePaywallClick = (action: string) => {
    trackExportPaywalled(action);
    setPaywallOpen(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            CSV Transaction Cleaner
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Upload your bank statement CSV and preview AI-powered categorization
          </p>
        </div>

        {/* Upload Area */}
        {!preview && (
          <Card className="mb-8">
            <CardBody>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  dragOver
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-700'
                }`}
              >
                <div className="space-y-4">
                  <div className="text-6xl">📄</div>
                  <div>
                    <p className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                      Drag & drop your CSV file here
                    </p>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      or click to browse (max 10 MB)
                    </p>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileInput}
                      className="hidden"
                      id="file-input"
                    />
                    <label htmlFor="file-input">
                      <Button color="primary" as="span">
                        Select File
                      </Button>
                    </label>
                  </div>
                </div>
              </div>
              {error && (
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded">
                  {error}
                </div>
              )}
            </CardBody>
          </Card>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Processing your CSV...</p>
          </div>
        )}

        {/* Preview Table */}
        {preview && !loading && (
          <div className="space-y-6">
            <Card>
              <CardBody>
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                      Preview ({preview.total_rows} rows total, showing first 50)
                    </h2>
                    {file && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        File: {file.name}
                      </p>
                    )}
                  </div>
                  <Button
                    color="default"
                    variant="light"
                    onClick={() => {
                      setPreview(null);
                      setFile(null);
                    }}
                  >
                    Upload New File
                  </Button>
                </div>

                <div className="overflow-x-auto">
                  <Table aria-label="Transaction preview">
                    <TableHeader>
                      <TableColumn>DATE</TableColumn>
                      <TableColumn>PAYEE</TableColumn>
                      <TableColumn>MEMO</TableColumn>
                      <TableColumn>AMOUNT</TableColumn>
                      <TableColumn>SUGGESTED ACCOUNT</TableColumn>
                      <TableColumn>CONFIDENCE</TableColumn>
                    </TableHeader>
                    <TableBody>
                      {preview.preview_rows.map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{row.date}</TableCell>
                          <TableCell>{row.payee}</TableCell>
                          <TableCell className="max-w-xs truncate">{row.memo}</TableCell>
                          <TableCell>${row.amount.toFixed(2)}</TableCell>
                          <TableCell>{row.suggested_account}</TableCell>
                          <TableCell>
                            <span
                              className={`px-2 py-1 rounded text-xs ${
                                row.confidence >= 0.8
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                  : row.confidence >= 0.5
                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                              }`}
                            >
                              {(row.confidence * 100).toFixed(0)}%
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardBody>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center">
              <Button
                color="primary"
                size="lg"
                onClick={() => handlePaywallClick('export_csv')}
                isDisabled
                className="opacity-50"
              >
                🔒 Export CSV
              </Button>
              <Button
                color="success"
                size="lg"
                onClick={() => handlePaywallClick('post_to_qbo')}
                isDisabled
                className="opacity-50"
              >
                🔒 Post to QuickBooks/Xero
              </Button>
            </div>

            <div className="text-center text-sm text-gray-600 dark:text-gray-400">
              Unlock export and posting features with a paid plan
            </div>
          </div>
        )}

        {/* Paywall Modal */}
        <Modal isOpen={paywallOpen} onClose={() => setPaywallOpen(false)} size="lg">
          <ModalContent>
            <ModalHeader className="flex flex-col gap-1">Upgrade Required</ModalHeader>
            <ModalBody>
              <p className="text-gray-600 dark:text-gray-300">
                Export and posting features are available on our paid plans starting at just $49/month.
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-300 mt-4">
                <li>Export cleaned CSV files</li>
                <li>Post directly to QuickBooks & Xero</li>
                <li>AI-powered categorization</li>
                <li>Automated journal entries</li>
                <li>OCR receipt scanning</li>
              </ul>
            </ModalBody>
            <ModalFooter>
              <Button color="default" variant="light" onClick={() => setPaywallOpen(false)}>
                Cancel
              </Button>
              <Button color="primary" as="a" href="/pricing">
                Choose a Plan
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    </div>
  );
}

