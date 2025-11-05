'use client';

/**
 * ColumnMapper Component
 * =======================
 * Confirm/adjust auto-detected column mappings
 */

import type { ColumnMapping } from '@/lib/parse/schema';

interface ColumnMapperProps {
  headers: string[];
  mapping: ColumnMapping;
  sampleRow: Record<string, string>;
  onMappingChange: (mapping: ColumnMapping) => void;
  onConfirm: () => void;
}

export function ColumnMapper({
  headers,
  mapping,
  sampleRow,
  onMappingChange,
  onConfirm,
}: ColumnMapperProps) {
  const updateMapping = (field: keyof ColumnMapping, value: number | undefined) => {
    onMappingChange({ ...mapping, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Confirm Column Mapping</h2>
        <p className="text-gray-600">We auto-detected these columns. Adjust if needed.</p>
      </div>

      <div className="grid gap-4">
        {/* Date */}
        <div className="flex items-center gap-4">
          <label className="w-32 font-medium">Date:</label>
          <select
            value={mapping.date ?? ''}
            onChange={(e) => updateMapping('date', e.target.value ? parseInt(e.target.value) : undefined)}
            className="flex-1 px-3 py-2 border rounded-md"
          >
            <option value="">-- Select --</option>
            {headers.map((h, i) => (
              <option key={i} value={i}>
                {h} ({sampleRow[h]})
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div className="flex items-center gap-4">
          <label className="w-32 font-medium">Description:</label>
          <select
            value={mapping.description ?? ''}
            onChange={(e) => updateMapping('description', e.target.value ? parseInt(e.target.value) : undefined)}
            className="flex-1 px-3 py-2 border rounded-md"
          >
            <option value="">-- Select --</option>
            {headers.map((h, i) => (
              <option key={i} value={i}>
                {h} ({sampleRow[h]})
              </option>
            ))}
          </select>
        </div>

        {/* Amount */}
        <div className="flex items-center gap-4">
          <label className="w-32 font-medium">Amount:</label>
          <select
            value={mapping.amount ?? ''}
            onChange={(e) => updateMapping('amount', e.target.value ? parseInt(e.target.value) : undefined)}
            className="flex-1 px-3 py-2 border rounded-md"
          >
            <option value="">-- Select (or use Debit/Credit) --</option>
            {headers.map((h, i) => (
              <option key={i} value={i}>
                {h} ({sampleRow[h]})
              </option>
            ))}
          </select>
        </div>

        {/* Optional: Debit/Credit */}
        {(!mapping.amount || mapping.debit !== undefined || mapping.credit !== undefined) && (
          <>
            <div className="flex items-center gap-4">
              <label className="w-32 font-medium">Debit:</label>
              <select
                value={mapping.debit ?? ''}
                onChange={(e) => updateMapping('debit', e.target.value ? parseInt(e.target.value) : undefined)}
                className="flex-1 px-3 py-2 border rounded-md"
              >
                <option value="">-- Optional --</option>
                {headers.map((h, i) => (
                  <option key={i} value={i}>
                    {h}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-4">
              <label className="w-32 font-medium">Credit:</label>
              <select
                value={mapping.credit ?? ''}
                onChange={(e) => updateMapping('credit', e.target.value ? parseInt(e.target.value) : undefined)}
                className="flex-1 px-3 py-2 border rounded-md"
              >
                <option value="">-- Optional --</option>
                {headers.map((h, i) => (
                  <option key={i} value={i}>
                    {h}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
      </div>

      <button
        onClick={onConfirm}
        disabled={!mapping.date || !mapping.description || (!mapping.amount && (!mapping.debit || !mapping.credit))}
        className="w-full px-6 py-3 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
      >
        Continue to Review
      </button>
    </div>
  );
}

