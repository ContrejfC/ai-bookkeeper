'use client';

/**
 * Free Categorizer v2 - Guided 4-Step Flow
 * ==========================================
 * Upload → Map Columns → Review & Edit → Export
 */

export const revalidate = 0; // Force fresh on every request

import { useState } from 'react';
import { Stepper } from '@/components/categorizer/Stepper';
import { UploadZone } from '@/components/categorizer/UploadZone';
import { ColumnMapper } from '@/components/categorizer/ColumnMapper';
import { ReviewTable } from '@/components/categorizer/ReviewTable';
import { ExportPanel } from '@/components/categorizer/ExportPanel';
import { SummaryStrip } from '@/components/categorizer/SummaryStrip';
import { parseCSV } from '@/lib/parse/csv';
import { parseOFX, isOFX } from '@/lib/parse/ofx';
import { parseQFX, isQFX } from '@/lib/parse/qfx';
import { categorizeTransactions } from '@/lib/categorize/pipeline';
import type { Transaction, ColumnMapping, ParsedData } from '@/lib/parse/schema';
import { getFlags } from '@/lib/flags';

const STEPS = ['Upload', 'Map Columns', 'Review', 'Export'];

export default function CategorizerV2Page() {
  const flags = getFlags();
  
  // State
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selected, setSelected] = useState(new Set<string>());
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // SSR marker for CI smoke tests

  // Step 1: File Upload
  const handleFileSelected = async (f: File) => {
    setError(null);
    setFile(f);
    
    try {
      const text = await f.text();
      const fileName = f.name.toLowerCase();
      
      let parsed: ParsedData;
      
      if (fileName.endsWith('.ofx') || isOFX(text)) {
        const txns = parseOFX(text);
        parsed = {
          transactions: txns,
          columnMapping: {},
          rowCount: txns.length,
          duplicateCount: txns.filter(t => t.duplicate).length,
        };
        // OFX doesn't need column mapping, skip to categorization
        setTransactions(txns);
        setStep(3);
        await categorizeParsed(txns);
        return;
      } else if (fileName.endsWith('.qfx') || isQFX(text)) {
        const txns = parseQFX(text);
        parsed = {
          transactions: txns,
          columnMapping: {},
          rowCount: txns.length,
          duplicateCount: txns.filter(t => t.duplicate).length,
        };
        setTransactions(txns);
        setStep(3);
        await categorizeParsed(txns);
        return;
      } else {
        parsed = parseCSV(text);
      }
      
      // Check row limit
      if (parsed.rowCount > flags.freeMaxRows) {
        setError(`File has ${parsed.rowCount} rows. Free tier limited to ${flags.freeMaxRows} rows.`);
        return;
      }
      
      setParsedData(parsed);
      setTransactions(parsed.transactions);
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Failed to parse file');
    }
  };

  // Step 2: Confirm Mapping
  const handleMappingConfirmed = async () => {
    if (!transactions.length) return;
    
    setIsProcessing(true);
    await categorizeParsed(transactions);
    setIsProcessing(false);
    setStep(3);
  };

  // Categorize transactions
  const categorizeParsed = async (txns: Transaction[]) => {
    const categorized = await categorizeTransactions(txns);
    setTransactions(categorized);
  };

  // Step 3: Edit Category
  const handleCategoryChange = (id: string, category: string) => {
    setTransactions(txns =>
      txns.map(t =>
        t.id === id
          ? { ...t, category, source: 'manual' as const, confidence: 1.0, needsReview: false }
          : t
      )
    );
  };

  const handleToggleSelect = (id: string) => {
    const newSet = new Set(selected);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelected(newSet);
  };

  // Step 4: Export
  const handleExportClick = () => {
    setStep(4);
  };

  const handleExport = (format: 'simple' | 'qbo') => {
    // Analytics tracked in ExportPanel
    console.log(`Exported ${transactions.length} transactions as ${format}`);
  };

  return (
    <main data-app="categorizer" data-version="v2" className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Free Bank Transaction Categorizer
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Upload → Auto-categorize → Verify → Download CSV or export to QuickBooks
          </p>
        </div>

        {/* Stepper */}
        <Stepper currentStep={step} steps={STEPS} />

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-8">
          <div className="lg:col-span-3">
            {/* Step 1: Upload */}
            {step === 1 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border p-8">
                <UploadZone onFileSelected={handleFileSelected} />
              </div>
            )}

            {/* Step 2: Map Columns */}
            {step === 2 && parsedData && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border p-8">
                <ColumnMapper
                  headers={Object.keys(transactions[0] || {})}
                  mapping={parsedData.columnMapping}
                  sampleRow={transactions[0] as any}
                  onMappingChange={(m) => setParsedData({ ...parsedData, columnMapping: m })}
                  onConfirm={handleMappingConfirmed}
                />
                {isProcessing && (
                  <div className="mt-4 text-center text-gray-600">
                    Categorizing transactions...
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Review */}
            {step === 3 && transactions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
                <div className="mb-4 flex justify-between items-center">
                  <h2 className="text-xl font-semibold">Review Categorized Transactions</h2>
                  <span className="text-sm text-gray-500">
                    {transactions.length} transactions
                  </span>
                </div>
                
                <ReviewTable
                  transactions={transactions}
                  selectedIds={selected}
                  onToggleSelect={handleToggleSelect}
                  onCategoryChange={handleCategoryChange}
                />

                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setStep(2)}
                    className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleExportClick}
                    className="flex-1 px-6 py-3 bg-emerald-600 text-white rounded-md hover:bg-emerald-700"
                  >
                    Continue to Export
                  </button>
                </div>
              </div>
            )}

            {/* Step 4: Export */}
            {step === 4 && transactions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border p-8">
                <ExportPanel transactions={transactions} onExport={handleExport} />
                
                <button
                  onClick={() => setStep(3)}
                  className="mt-4 px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Back to Review
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          {step >= 3 && transactions.length > 0 && (
            <div className="lg:col-span-1">
              <SummaryStrip transactions={transactions} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

