'use client';

/**
 * ReviewTable Component
 * ======================
 * Simple table for reviewing categorized transactions
 * (Simplified version - virtualization can be added later)
 */

import type { Transaction } from '@/lib/parse/schema';
import { getCategoryNames } from '@/lib/categories';

interface ReviewTableProps {
  transactions: Transaction[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onCategoryChange: (id: string, category: string) => void;
}

export function ReviewTable({
  transactions,
  selectedIds,
  onToggleSelect,
  onCategoryChange,
}: ReviewTableProps) {
  const categories = getCategoryNames();

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-3 py-2">
              <input type="checkbox" aria-label="Select all" />
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
          {transactions.slice(0, 100).map((txn) => (
            <tr
              key={txn.id}
              className={`${selectedIds.has(txn.id) ? 'bg-emerald-50 dark:bg-emerald-900/20' : ''} ${txn.duplicate ? 'bg-yellow-50 dark:bg-yellow-900/20' : ''}`}
            >
              <td className="px-3 py-2">
                <input
                  type="checkbox"
                  checked={selectedIds.has(txn.id)}
                  onChange={() => onToggleSelect(txn.id)}
                  aria-label={`Select transaction ${txn.description}`}
                />
              </td>
              <td className="px-3 py-2 text-sm">{txn.date.toLocaleDateString()}</td>
              <td className="px-3 py-2 text-sm">{txn.description}</td>
              <td className="px-3 py-2 text-sm text-right">${txn.amount.toFixed(2)}</td>
              <td className="px-3 py-2">
                <select
                  value={txn.category || ''}
                  onChange={(e) => onCategoryChange(txn.id, e.target.value)}
                  className="text-sm px-2 py-1 border rounded"
                >
                  <option value="">-- Select --</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </td>
              <td className="px-3 py-2 text-center">
                {txn.confidence && (
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      txn.confidence >= 0.9
                        ? 'bg-green-100 text-green-800'
                        : txn.confidence >= 0.7
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {(txn.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {transactions.length > 100 && (
        <div className="py-4 text-center text-sm text-gray-500">
          Showing first 100 of {transactions.length} transactions
        </div>
      )}
    </div>
  );
}

