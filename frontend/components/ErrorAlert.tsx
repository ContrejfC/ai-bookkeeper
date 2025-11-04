/**
 * Error Alert Component with Repair Tips
 * ======================================
 * 
 * Displays error messages with actionable repair tips.
 */

'use client';

import { Card, CardBody, Link } from '@nextui-org/react';
import { type FreeToolError } from '@/lib/errors';

interface ErrorAlertProps {
  error: FreeToolError;
  onDismiss?: () => void;
}

export function ErrorAlert({ error, onDismiss }: ErrorAlertProps) {
  return (
    <Card className="border-2 border-red-300 bg-red-50">
      <CardBody className="p-6">
        <div className="flex items-start gap-3">
          <span className="text-red-600 text-2xl flex-shrink-0" aria-hidden="true">⚠️</span>
          <div className="flex-1">
            <div className="flex items-start justify-between gap-4">
              <h3 className="text-red-900 font-bold">{error.message}</h3>
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded px-2"
                  aria-label="Dismiss error"
                >
                  ✕
                </button>
              )}
            </div>
            
            {error.repairTips.length > 0 && (
              <div className="text-red-800 text-sm mt-3">
                <strong>How to fix:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  {error.repairTips.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {error.helpLink && (
              <div className="mt-3">
                <Link 
                  href={error.helpLink}
                  className="text-blue-600 hover:underline text-sm font-medium inline-flex items-center gap-1"
                >
                  Learn more →
                </Link>
              </div>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

