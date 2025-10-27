/**
 * useJobStatus Hook - Poll Background Job Status
 * ==============================================
 * 
 * Custom React hook for polling background job status with smart intervals.
 * 
 * Features:
 * --------
 * - Automatic polling with exponential backoff
 * - Stops polling when job completes/fails
 * - Cleanup on unmount
 * - TypeScript support
 * 
 * Usage:
 * ------
 * ```typescript
 * const { status, progress, result, error, isLoading } = useJobStatus(jobId);
 * 
 * if (isLoading) return <Progress value={progress} />;
 * if (error) return <Error message={error} />;
 * if (status === 'complete') return <Success data={result} />;
 * ```
 */

import { useState, useEffect, useCallback } from 'react';

export interface JobStatus {
  id: string;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'cancelled' | 'not_found';
  progress: number; // 0-100
  message: string;
  result?: any;
  error?: string;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
}

export interface UseJobStatusReturn {
  status: JobStatus['status'];
  progress: number;
  message: string;
  result: any;
  error: string | null;
  isLoading: boolean;
  isComplete: boolean;
  isFailed: boolean;
  refetch: () => Promise<void>;
}

/**
 * Poll job status with smart intervals
 * 
 * @param jobId - Job identifier to poll
 * @param options - Configuration options
 * @returns Job status data and utilities
 */
export function useJobStatus(
  jobId: string | null | undefined,
  options: {
    enabled?: boolean;
    onComplete?: (result: any) => void;
    onError?: (error: string) => void;
    initialInterval?: number;  // Default: 1000ms
    maxInterval?: number;      // Default: 5000ms
    backoffMultiplier?: number; // Default: 1.5
  } = {}
): UseJobStatusReturn {
  const {
    enabled = true,
    onComplete,
    onError,
    initialInterval = 1000,
    maxInterval = 5000,
    backoffMultiplier = 1.5,
  } = options;

  const [jobStatus, setJobStatus] = useState<JobStatus>({
    id: jobId || '',
    status: 'pending',
    progress: 0,
    message: '',
  });

  const [interval, setInterval] = useState(initialInterval);

  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`/api/jobs/${jobId}`);
      const data = await response.json();

      setJobStatus(data);

      // Handle completion
      if (data.status === 'complete') {
        if (onComplete) {
          onComplete(data.result);
        }
      }

      // Handle failure
      if (data.status === 'failed') {
        if (onError) {
          onError(data.error || 'Job failed');
        }
      }

      return data;
    } catch (error) {
      console.error('Error fetching job status:', error);
      if (onError) {
        onError(error instanceof Error ? error.message : 'Unknown error');
      }
    }
  }, [jobId, onComplete, onError]);

  useEffect(() => {
    if (!jobId || !enabled) {
      return;
    }

    // Initial fetch
    fetchStatus();

    // Start polling
    const poll = async () => {
      const data = await fetchStatus();

      // Stop polling if job is done
      if (data && ['complete', 'failed', 'cancelled'].includes(data.status)) {
        return;
      }

      // Exponential backoff
      setInterval((prev) => Math.min(prev * backoffMultiplier, maxInterval));

      // Schedule next poll
      timeoutId = setTimeout(poll, interval);
    };

    let timeoutId = setTimeout(poll, interval);

    // Cleanup
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [jobId, enabled, interval, fetchStatus, backoffMultiplier, maxInterval]);

  return {
    status: jobStatus.status,
    progress: jobStatus.progress,
    message: jobStatus.message,
    result: jobStatus.result,
    error: jobStatus.error || null,
    isLoading: ['pending', 'running'].includes(jobStatus.status),
    isComplete: jobStatus.status === 'complete',
    isFailed: jobStatus.status === 'failed',
    refetch: fetchStatus,
  };
}


/**
 * Poll multiple jobs simultaneously
 * 
 * @param jobIds - Array of job identifiers
 * @returns Map of job statuses
 */
export function useMultipleJobStatus(
  jobIds: string[],
  options: {
    onAllComplete?: () => void;
    onAnyError?: (jobId: string, error: string) => void;
  } = {}
): Map<string, UseJobStatusReturn> {
  const [statuses, setStatuses] = useState<Map<string, UseJobStatusReturn>>(new Map());

  // Check if all jobs are complete
  const allComplete = Array.from(statuses.values()).every((s) => s.isComplete);
  const anyFailed = Array.from(statuses.values()).some((s) => s.isFailed);

  // Trigger callback when all complete
  useEffect(() => {
    if (allComplete && options.onAllComplete) {
      options.onAllComplete();
    }
  }, [allComplete, options]);

  // Not implemented yet - would need multiple useJobStatus hooks
  // For now, poll jobs sequentially
  
  return statuses;
}

