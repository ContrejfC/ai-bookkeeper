'use client';

/**
 * ResultsPreview Component
 * 
 * Shows preview of categorized transactions with confidence scores.
 * Displays first 25 rows before email gate.
 * Includes interactive feedback for low-confidence transactions.
 */

import React, { useState } from 'react';
import { trackPreviewView, trackUpgradeClick } from '@/lib/telemetry';
import { CategoryFeedback, FeedbackSummary } from './CategoryFeedback';

interface Transaction {
  id?: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  confidence: number;
  notes?: string;
  suggested_categories?: string[];
}

interface ResultsPreviewProps {
  uploadId: string;
  previewRows: Transaction[];
  totalRows: number;
  categoriesCount: number;
  confidenceAvg: number;
  onContinue: () => void;
  onFeedbackCollected?: (feedback: Record<string, string>) => void;
}

export function ResultsPreview({
  uploadId,
  previewRows,
  totalRows,
  categoriesCount,
  confidenceAvg,
  onContinue,
  onFeedbackCollected
}: ResultsPreviewProps) {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [feedbackMode, setFeedbackMode] = useState(false);
  const [userFeedback, setUserFeedback] = useState<Record<string, string>>({});
  const [currentFeedbackIndex, setCurrentFeedbackIndex] = useState(0);
  const [showFeedbackSummary, setShowFeedbackSummary] = useState(false);
  
  const cappedRows = totalRows > 500;
  const exportableRows = Math.min(totalRows, 500);

  // Identify low-confidence transactions (< 0.85)
  const lowConfidenceTransactions = previewRows
    .map((row, idx) => ({ ...row, id: row.id || `txn_${idx}` }))
    .filter(row => row.confidence < 0.85);
  
  const hasLowConfidence = lowConfidenceTransactions.length > 0;

  // Track preview view on mount
  React.useEffect(() => {
    trackPreviewView({
      upload_id: uploadId,
      rows_total: totalRows,
      categories_count: categoriesCount,
      confidence_avg: confidenceAvg,
      low_confidence_count: lowConfidenceTransactions.length
    });
  }, [uploadId, totalRows, categoriesCount, confidenceAvg, lowConfidenceTransactions.length]);

  const handleUpgradeClick = (location: string) => {
    trackUpgradeClick({
      upload_id: uploadId,
      cta_location: location
    });
    
    window.open('/pricing?utm_source=free_tool&utm_medium=preview&utm_campaign=upgrade', '_blank');
  };

  // Feedback handlers
  const handleStartFeedback = () => {
    setFeedbackMode(true);
    setCurrentFeedbackIndex(0);
  };

  const handleFeedback = (transactionId: string, selectedCategory: string) => {
    // Save feedback
    setUserFeedback(prev => ({
      ...prev,
      [transactionId]: selectedCategory
    }));

    // Move to next transaction or show summary
    if (currentFeedbackIndex < lowConfidenceTransactions.length - 1) {
      setCurrentFeedbackIndex(prev => prev + 1);
    } else {
      // All feedback collected
      setShowFeedbackSummary(true);
    }
  };

  const handleSkip = (transactionId: string) => {
    // Move to next without saving feedback
    if (currentFeedbackIndex < lowConfidenceTransactions.length - 1) {
      setCurrentFeedbackIndex(prev => prev + 1);
    } else {
      // Done with all transactions
      setShowFeedbackSummary(true);
    }
  };

  const handleContinueAfterFeedback = () => {
    // Pass feedback to parent
    if (onFeedbackCollected && Object.keys(userFeedback).length > 0) {
      onFeedbackCollected(userFeedback);
    }
    setFeedbackMode(false);
    setShowFeedbackSummary(false);
    onContinue();
  };

  const handleSkipAllFeedback = () => {
    setFeedbackMode(false);
    onContinue();
  };

  // If in feedback mode, show feedback UI
  if (feedbackMode && !showFeedbackSummary) {
    const currentTransaction = lowConfidenceTransactions[currentFeedbackIndex];
    return (
      <div className="w-full max-w-4xl mx-auto">
        {/* Progress Indicator */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Transaction {currentFeedbackIndex + 1} of {lowConfidenceTransactions.length}</span>
            <span>{Object.keys(userFeedback).length} feedback provided</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${((currentFeedbackIndex + 1) / lowConfidenceTransactions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Category Feedback Component */}
        <CategoryFeedback
          transaction={currentTransaction}
          onFeedback={handleFeedback}
          onSkip={handleSkip}
        />

        {/* Skip All Button */}
        <div className="mt-4 text-center">
          <button
            onClick={handleSkipAllFeedback}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Skip all remaining questions →
          </button>
        </div>
      </div>
    );
  }

  // If showing summary, display feedback summary
  if (showFeedbackSummary) {
    return (
      <FeedbackSummary
        totalTransactions={lowConfidenceTransactions.length}
        feedbackProvided={Object.keys(userFeedback).length}
        onContinue={handleContinueAfterFeedback}
      />
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm font-medium text-gray-600">Total Transactions</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">{totalRows}</div>
          {cappedRows && (
            <div className="mt-2 text-xs text-amber-600">
              ⚠️ Free tier exports first 500 rows
            </div>
          )}
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm font-medium text-gray-600">Categories Found</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">{categoriesCount}</div>
          <div className="mt-2 text-xs text-gray-500">
            AI-powered categorization
          </div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="text-sm font-medium text-gray-600">Avg. Confidence</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {(confidenceAvg * 100).toFixed(0)}%
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {confidenceAvg >= 0.9 ? '✨ Excellent' : confidenceAvg >= 0.8 ? '✓ Good' : '⚠️ Review recommended'}
          </div>
        </div>
      </div>

      {/* Upgrade CTA Banner */}
      {cappedRows && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Your statement has {totalRows} rows
              </h3>
              <p className="mt-1 text-sm text-gray-600">
                Free tier exports the first 500 rows. Upgrade to export all {totalRows} rows without limits.
              </p>
            </div>
            <button
              onClick={() => handleUpgradeClick('preview_banner')}
              className="ml-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
            >
              View Pricing →
            </button>
          </div>
        </div>
      )}

      {/* Feedback Prompt Banner - Show if there are low confidence transactions */}
      {hasLowConfidence && (
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-300 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <span className="text-3xl">🤔</span>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                Help Improve Our AI! (Optional)
              </h3>
              <p className="text-sm text-gray-700 mb-3">
                We found <strong>{lowConfidenceTransactions.length} transaction{lowConfidenceTransactions.length !== 1 ? 's' : ''}</strong> where 
                our AI isn't fully confident. Would you help us categorize {lowConfidenceTransactions.length > 1 ? 'them' : 'it'}?
              </p>
              <p className="text-xs text-gray-600 mb-4">
                ⏱️ Takes about {Math.ceil(lowConfidenceTransactions.length * 15 / 60)} minute{Math.ceil(lowConfidenceTransactions.length * 15 / 60) !== 1 ? 's' : ''} • 
                Your feedback trains our model for everyone • Completely optional
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleStartFeedback}
                  className="px-5 py-2.5 bg-yellow-600 text-white font-medium rounded-lg hover:bg-yellow-700 transition-colors"
                >
                  Help Categorize ({lowConfidenceTransactions.length})
                </button>
                <button
                  onClick={onContinue}
                  className="px-5 py-2.5 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Skip & Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900">
            Preview (First {previewRows.length} Rows)
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Enter your email below to download the full CSV with {exportableRows} categorized transactions.
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {previewRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.date}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-md truncate">{row.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                    <span className={row.amount < 0 ? 'text-red-600' : 'text-green-600'}>
                      ${Math.abs(row.amount).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {row.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <ConfidenceBadge confidence={row.confidence} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {previewRows.length < exportableRows && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-600">
              + {exportableRows - previewRows.length} more rows available after email verification
            </p>
          </div>
        )}
      </div>

      {/* Continue Button */}
      <div className="flex justify-center">
        <button
          onClick={onContinue}
          className="px-8 py-3 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
        >
          Continue to Download →
        </button>
      </div>

      {/* Disclaimers */}
      <div className="text-center space-y-2">
        <p className="text-sm text-gray-600">
          🔒 Your privacy matters. Files auto-delete after 24 hours.
        </p>
        <p className="text-xs text-gray-500">
          Not financial advice. Always review with a professional accountant.
        </p>
      </div>
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = (confidence * 100).toFixed(0);
  
  let color = 'gray';
  let label = 'Low';
  
  if (confidence >= 0.9) {
    color = 'green';
    label = 'High';
  } else if (confidence >= 0.75) {
    color = 'blue';
    label = 'Good';
  } else if (confidence >= 0.6) {
    color = 'yellow';
    label = 'Fair';
  } else {
    color = 'red';
    label = 'Low';
  }
  
  const colorClasses = {
    green: 'bg-green-100 text-green-800',
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    red: 'bg-red-100 text-red-800',
    gray: 'bg-gray-100 text-gray-800'
  };
  
  return (
    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
      {percentage}%
    </span>
  );
}

