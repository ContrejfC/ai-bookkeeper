'use client';

/**
 * ExportPanel Component
 * ======================
 * Format selection and download buttons
 */

import type { Transaction } from '@/lib/parse/schema';
import { exportSimpleCSV } from '@/lib/export/csv_simple';
import { exportQBOCSV } from '@/lib/export/csv_qbo';
import { useState } from 'react';

interface ExportPanelProps {
  transactions: Transaction[];
  onExport: (format: 'simple' | 'qbo') => void;
}

export function ExportPanel({ transactions, onExport }: ExportPanelProps) {
  const [format, setFormat] = useState<'simple' | 'qbo'>('simple');
  
  const lowConfidenceCount = transactions.filter(t => (t.confidence || 0) < 0.7).length;

  const handleDownload = () => {
    const csv = format === 'simple'
      ? exportSimpleCSV(transactions)
      : exportQBOCSV(transactions);
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions_${format}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    onExport(format);
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold mb-2">Export Format</h3>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={format === 'simple'}
              onChange={() => setFormat('simple')}
              className="w-4 h-4"
            />
            <span>Simple CSV (all fields)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={format === 'qbo'}
              onChange={() => setFormat('qbo')}
              className="w-4 h-4"
            />
            <span>QuickBooks CSV</span>
          </label>
        </div>
      </div>

      {lowConfidenceCount > 0 && (
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            ⚠️ {lowConfidenceCount} transactions have low confidence (&lt;70%). Review before exporting.
          </p>
        </div>
      )}

      <button
        onClick={handleDownload}
        className="w-full px-6 py-3 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition font-medium"
      >
        Download CSV
      </button>
    </div>
  );
}

