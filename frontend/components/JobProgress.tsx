/**
 * JobProgress Component - Display Background Job Progress
 * =======================================================
 * 
 * UI component for showing background job status with progress bar.
 * 
 * Features:
 * --------
 * - Real-time progress updates
 * - Status messages
 * - Error handling
 * - Success/failure states
 * - Customizable appearance
 * 
 * Usage:
 * ------
 * ```tsx
 * <JobProgress 
 *   jobId={jobId}
 *   onComplete={(result) => console.log('Done!', result)}
 *   title="Processing Transactions"
 * />
 * ```
 */

'use client';

import React from 'react';
import { Card, CardBody, Progress, Button } from '@nextui-org/react';
import { useJobStatus } from '@/hooks/useJobStatus';

export interface JobProgressProps {
  jobId: string | null | undefined;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
  title?: string;
  showDetails?: boolean;
  className?: string;
}

export function JobProgress({
  jobId,
  onComplete,
  onError,
  title = 'Processing...',
  showDetails = true,
  className = '',
}: JobProgressProps) {
  const { status, progress, message, result, error, isLoading, isComplete, isFailed } = 
    useJobStatus(jobId, { onComplete, onError });

  if (!jobId) {
    return null;
  }

  // Status colors
  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'primary';
      case 'complete':
        return 'success';
      case 'failed':
        return 'danger';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  // Status icon
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return '⏳';
      case 'complete':
        return '✅';
      case 'failed':
        return '❌';
      case 'pending':
        return '⏱️';
      default:
        return '❓';
    }
  };

  return (
    <Card className={className}>
      <CardBody className="gap-4">
        {/* Title */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getStatusIcon()}</span>
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>

        {/* Progress Bar */}
        <Progress
          value={progress}
          color={getStatusColor()}
          size="md"
          showValueLabel
          label={message || status}
          className="w-full"
        />

        {/* Status Message */}
        {showDetails && (
          <div className="text-sm">
            <p className="text-default-600">{message}</p>
            {status === 'running' && (
              <p className="text-default-400 mt-1">
                {progress}% complete
              </p>
            )}
          </div>
        )}

        {/* Error Message */}
        {isFailed && error && (
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-3">
            <p className="text-danger-700 text-sm font-medium">Error:</p>
            <p className="text-danger-600 text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {isComplete && showDetails && (
          <div className="bg-success-50 border border-success-200 rounded-lg p-3">
            <p className="text-success-700 text-sm font-medium">
              ✓ Job completed successfully!
            </p>
            {result && (
              <pre className="text-success-600 text-xs mt-2 overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>
        )}

        {/* Job ID (for debugging) */}
        {showDetails && (
          <p className="text-xs text-default-400">
            Job ID: {jobId}
          </p>
        )}
      </CardBody>
    </Card>
  );
}


/**
 * Compact progress indicator (for inline use)
 */
export function JobProgressCompact({
  jobId,
  onComplete,
}: {
  jobId: string | null | undefined;
  onComplete?: (result: any) => void;
}) {
  const { status, progress, message, isLoading } = useJobStatus(jobId, { onComplete });

  if (!jobId || !isLoading) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <Progress
        value={progress}
        size="sm"
        color="primary"
        className="w-32"
      />
      <span className="text-default-600">{message}</span>
    </div>
  );
}


/**
 * Progress modal (full-screen overlay)
 */
export function JobProgressModal({
  jobId,
  onComplete,
  onClose,
  title = 'Processing...',
}: {
  jobId: string | null | undefined;
  onComplete?: (result: any) => void;
  onClose?: () => void;
  title?: string;
}) {
  const { isComplete, isFailed } = useJobStatus(jobId, { onComplete });

  if (!jobId) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="max-w-md w-full">
        <JobProgress
          jobId={jobId}
          title={title}
          showDetails={true}
        />
        
        {(isComplete || isFailed) && onClose && (
          <Button
            color="primary"
            onClick={onClose}
            className="mt-4 w-full"
          >
            Close
          </Button>
        )}
      </div>
    </div>
  );
}

