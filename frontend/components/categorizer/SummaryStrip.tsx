'use client';

/**
 * SummaryStrip Component
 * =======================
 * Shows stats: total, by category, needing review, duplicates
 */

import type { Transaction } from '@/lib/parse/schema';

interface SummaryStripProps {
  transactions: Transaction[];
}

export function SummaryStrip({ transactions }: SummaryStripProps) {
  const total = transactions.length;
  const needsReview = transactions.filter(t => t.needsReview).length;
  const duplicates = transactions.filter(t => t.duplicate).length;
  
  // Count by category
  const byCategory = transactions.reduce((acc, t) => {
    const cat = t.category || 'Uncategorized';
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const topCategories = Object.entries(byCategory)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border p-4 space-y-4">
      <h3 className="font-semibold text-lg">Summary</h3>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Total Transactions:</span>
          <span className="font-medium">{total}</span>
        </div>
        
        {needsReview > 0 && (
          <div className="flex justify-between text-sm text-yellow-600">
            <span>Needs Review:</span>
            <span className="font-medium">{needsReview}</span>
          </div>
        )}
        
        {duplicates > 0 && (
          <div className="flex justify-between text-sm text-orange-600">
            <span>Possible Duplicates:</span>
            <span className="font-medium">{duplicates}</span>
          </div>
        )}
      </div>

      <div className="border-t pt-3">
        <h4 className="text-sm font-medium mb-2">Top Categories</h4>
        <div className="space-y-1">
          {topCategories.map(([cat, count]) => (
            <div key={cat} className="flex justify-between text-sm">
              <span className="truncate">{cat}</span>
              <span className="text-gray-500">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

