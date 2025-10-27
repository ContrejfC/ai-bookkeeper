/**
 * Background Jobs Demo Page
 * =========================
 * 
 * This page demonstrates how to use the background jobs system:
 * - Upload and categorize transactions
 * - Process OCR on receipts
 * - Export to QuickBooks
 * - Monitor job progress with real-time updates
 */

'use client';

import React, { useState } from 'react';
import { 
  Card, 
  CardBody, 
  CardHeader, 
  Button, 
  Input,
  Divider,
  Chip,
  Accordion,
  AccordionItem
} from '@nextui-org/react';
import { JobProgress, JobProgressCompact } from '@/components/JobProgress';
import { useAuth } from '@/contexts/auth-context';

export default function BackgroundJobsPage() {
  const { user } = useAuth();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [recentJobs, setRecentJobs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // ============================================================================
  // Start Categorization Job
  // ============================================================================
  const handleStartCategorization = async () => {
    if (!user) return;

    // Get tenant ID from user (handle both single string and array)
    const tenantId = Array.isArray(user.tenant_ids) 
      ? user.tenant_ids[0] 
      : user.tenant_ids || 'demo-tenant';

    setIsLoading(true);
    try {
      const response = await fetch('/api/jobs/categorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: tenantId,  // Using tenant_id as company_id
          tenant_id: tenantId,
          limit: 100
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setActiveJobId(data.job_id);
        setRecentJobs([data.job_id, ...recentJobs.slice(0, 4)]);
      } else {
        alert(`Error: ${data.detail || 'Failed to start job'}`);
      }
    } catch (error) {
      console.error('Error starting categorization:', error);
      alert('Failed to start job');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // Start OCR Job
  // ============================================================================
  const handleStartOCR = async () => {
    if (!user) return;

    const tenantId = Array.isArray(user.tenant_ids) 
      ? user.tenant_ids[0] 
      : user.tenant_ids || 'demo-tenant';

    setIsLoading(true);
    try {
      const response = await fetch('/api/jobs/ocr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: tenantId,
          receipt_id: 'receipt-' + Date.now(),
          file_path: '/tmp/sample-receipt.jpg'  // Mock path
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setActiveJobId(data.job_id);
        setRecentJobs([data.job_id, ...recentJobs.slice(0, 4)]);
      } else {
        alert(`Error: ${data.detail || 'Failed to start job'}`);
      }
    } catch (error) {
      console.error('Error starting OCR:', error);
      alert('Failed to start job');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // Start Export Job
  // ============================================================================
  const handleStartExport = async () => {
    if (!user) return;

    const tenantId = Array.isArray(user.tenant_ids) 
      ? user.tenant_ids[0] 
      : user.tenant_ids || 'demo-tenant';

    setIsLoading(true);
    try {
      const response = await fetch('/api/jobs/export-qbo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_id: tenantId,
          tenant_id: tenantId,
          start_date: '2025-01-01',
          end_date: '2025-12-31'
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setActiveJobId(data.job_id);
        setRecentJobs([data.job_id, ...recentJobs.slice(0, 4)]);
      } else {
        alert(`Error: ${data.detail || 'Failed to start job'}`);
      }
    } catch (error) {
      console.error('Error starting export:', error);
      alert('Failed to start job');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // Upload File
  // ============================================================================
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!user || !event.target.files || event.target.files.length === 0) return;

    const tenantId = Array.isArray(user.tenant_ids) 
      ? user.tenant_ids[0] 
      : user.tenant_ids || 'demo-tenant';

    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', tenantId);
    formData.append('tenant_id', tenantId);

    setIsLoading(true);
    try {
      const response = await fetch('/api/jobs/upload-and-categorize', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (response.ok) {
        setActiveJobId(data.job_id);
        setRecentJobs([data.job_id, ...recentJobs.slice(0, 4)]);
      } else {
        alert(`Error: ${data.detail || 'Failed to upload file'}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // Render
  // ============================================================================
  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Background Jobs Demo</h1>
        <p className="text-default-600">
          Test long-running operations with real-time progress tracking
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Actions */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">Start New Job</h2>
            </CardHeader>
            <CardBody className="gap-4">
              {/* Categorization */}
              <div>
                <h3 className="text-sm font-medium mb-2">🤖 AI Categorization</h3>
                <p className="text-xs text-default-500 mb-3">
                  Categorize uncategorized transactions using AI
                </p>
                <Button
                  color="primary"
                  onClick={handleStartCategorization}
                  isLoading={isLoading}
                  className="w-full"
                >
                  Start Categorization
                </Button>
              </div>

              <Divider />

              {/* OCR */}
              <div>
                <h3 className="text-sm font-medium mb-2">📸 Receipt OCR</h3>
                <p className="text-xs text-default-500 mb-3">
                  Extract data from receipt images
                </p>
                <Button
                  color="secondary"
                  onClick={handleStartOCR}
                  isLoading={isLoading}
                  className="w-full"
                >
                  Process Receipt
                </Button>
              </div>

              <Divider />

              {/* Export */}
              <div>
                <h3 className="text-sm font-medium mb-2">📤 QuickBooks Export</h3>
                <p className="text-xs text-default-500 mb-3">
                  Export journal entries to QuickBooks Online
                </p>
                <Button
                  color="success"
                  onClick={handleStartExport}
                  isLoading={isLoading}
                  className="w-full"
                >
                  Export to QBO
                </Button>
              </div>

              <Divider />

              {/* File Upload */}
              <div>
                <h3 className="text-sm font-medium mb-2">📁 Upload & Categorize</h3>
                <p className="text-xs text-default-500 mb-3">
                  Upload transactions file and start categorization
                </p>
                <Input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileUpload}
                  disabled={isLoading}
                />
              </div>
            </CardBody>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">How It Works</h2>
            </CardHeader>
            <CardBody>
              <ol className="list-decimal list-inside space-y-2 text-sm">
                <li>Click a button to start a background job</li>
                <li>Job runs asynchronously on the server</li>
                <li>Progress updates automatically every 1-5 seconds</li>
                <li>Get notified when complete or failed</li>
                <li>View job results and history</li>
              </ol>
            </CardBody>
          </Card>
        </div>

        {/* Right Column: Progress */}
        <div className="space-y-4">
          {/* Active Job */}
          {activeJobId && (
            <JobProgress
              jobId={activeJobId}
              title="Current Job"
              showDetails={true}
              onComplete={(result) => {
                console.log('Job completed:', result);
                // Optionally refresh data
              }}
              onError={(error) => {
                console.error('Job failed:', error);
              }}
            />
          )}

          {/* Recent Jobs */}
          {recentJobs.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-xl font-semibold">Recent Jobs</h2>
              </CardHeader>
              <CardBody>
                <Accordion>
                  {recentJobs.map((jobId) => (
                    <AccordionItem
                      key={jobId}
                      title={
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-default-500">
                            {jobId}
                          </span>
                        </div>
                      }
                    >
                      <JobProgressCompact
                        jobId={jobId}
                        onComplete={() => {}}
                      />
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardBody>
            </Card>
          )}

          {/* Documentation */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold">API Usage</h2>
            </CardHeader>
            <CardBody>
              <pre className="text-xs bg-default-100 p-3 rounded-lg overflow-auto">
{`// Start a job
const response = await fetch('/api/jobs/categorize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company_id: 'demo-company',
    tenant_id: 'demo-tenant',
    limit: 100
  })
});

const { job_id } = await response.json();

// Poll for status
const status = await fetch(\`/api/jobs/\${job_id}\`);
const data = await status.json();

console.log(data.progress); // 0-100
console.log(data.status);   // pending/running/complete
console.log(data.result);   // final result`}
              </pre>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

