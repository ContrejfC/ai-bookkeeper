'use client';

/**
 * Confidence Badge with Tooltip
 * ===============================
 * Color-coded confidence indicator: green ≥0.75, yellow 0.55-0.74, red <0.55
 */

import type { Explanation } from '@/lib/parse/schema';

interface ConfidenceBadgeProps {
  confidence: number;
  explanation?: Explanation;
}

export function ConfidenceBadge({ confidence, explanation }: ConfidenceBadgeProps) {
  const percent = Math.round(confidence * 100);
  
  const color =
    confidence >= 0.75
      ? 'bg-green-100 text-green-800 border-green-200'
      : confidence >= 0.55
      ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
      : confidence >= 0.35
      ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
      : 'bg-red-100 text-red-800 border-red-200';

  const label =
    confidence >= 0.75 ? 'High' : confidence >= 0.55 ? 'Medium' : 'Low';

  const tooltip = explanation
    ? `${label} confidence (${percent}%)\nSource: ${explanation.stage}\n${
        explanation.ruleName || explanation.topMatch || explanation.llmHint || ''
      }`
    : `${label} confidence (${percent}%)`;

  return (
    <span
      className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded border ${color}`}
      title={tooltip}
    >
      {label}
    </span>
  );
}

