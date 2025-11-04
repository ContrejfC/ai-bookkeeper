'use client';

/**
 * Free Categorizer Page v2 - Trust, Compliance, and Conversion
 * =============================================================
 * 
 * Enhanced with:
 * - Consent toggle (default OFF)
 * - Sample data
 * - Email gate with bypass
 * - Error states with repair tips
 * - Delete functionality
 * - Accessibility improvements
 */

import React, { useState, useEffect } from 'react';
import { Button, Checkbox, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure, Link, Card, CardBody } from '@nextui-org/react';
import { FreeDropzone } from '@/components/FreeDropzone';
import { ResultsPreview } from '@/components/ResultsPreview';
import { ErrorAlert } from '@/components/ErrorAlert';
import { FreeCategorizerContent } from '@/components/FreeCategorizerContent';
import { sendVerificationCode, verifyEmailCode, exportCategorizedCSV, saveFeedback, deleteUpload } from './actions';
import { 
  trackUploadStarted, 
  trackParseOk, 
  trackPreviewViewed, 
  trackVerifyClicked,
  trackDownloadClicked, 
  trackUpgradeClicked, 
  trackDeleteClicked,
  trackLeadSubmitted 
} from '@/lib/analytics';
import { getErrorDetails, type ErrorCode } from '@/lib/errors';
import { getFreeToolConfig } from '@/lib/config';

type Step = 'upload' | 'processing' | 'preview' | 'email' | 'verify' | 'download' | 'complete';

// Sample data for demonstration
const SAMPLE_CSV_DATA = `date,description,amount,category
2024-10-01,Amazon.com,-127.45,Office Supplies
2024-10-02,Stripe Payment,3000.00,Revenue
2024-10-03,Google Workspace,-12.00,Software
2024-10-05,Electric Company,-156.89,Utilities
2024-10-07,Client Payment Inc,2500.00,Revenue
2024-10-08,Office Depot,-67.43,Office Supplies
2024-10-10,Verizon Wireless,-89.99,Telecom
2024-10-12,FedEx Shipping,-45.20,Shipping`;

export default function FreeCategorizerPage() {
  const config = getFreeToolConfig();
  
  // State
  const [step, setStep] = useState<Step>('upload');
  const [uploadId, setUploadId] = useState<string>('');
  const [filename, setFilename] = useState<string>('');
  const [previewRows, setPreviewRows] = useState<any[]>([]);
  const [totalRows, setTotalRows] = useState<number>(0);
  const [categoriesCount, setCategoriesCount] = useState<number>(0);
  const [confidenceAvg, setConfidenceAvg] = useState<number>(0);
  const [email, setEmail] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [error, setError] = useState<ErrorCode | null>(null);
  const [errorContext, setErrorContext] = useState<Record<string, any>>({});
  const [consentTraining, setConsentTraining] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [bypassedEmail, setBypassedEmail] = useState(false);
  
  // Modals
  const sampleModal = useDisclosure();
  const deleteModal = useDisclosure();
  const qboModal = useDisclosure();
  
  // Track sample modal open
  const handleSampleClick = () => {
    // Load sample data into preview
    const sampleRows = SAMPLE_CSV_DATA.split('\n').slice(1).map((line, idx) => {
      const [date, description, amount, category] = line.split(',');
      return {
        id: `sample_${idx}`,
        date,
        description,
        amount: parseFloat(amount),
        category,
        confidence: 0.95
      };
    });
    
    setUploadId('sample_upload');
    setFilename('sample_statement.csv');
    setPreviewRows(sampleRows);
    setTotalRows(sampleRows.length);
    setCategoriesCount(new Set(sampleRows.map(r => r.category)).size);
    setConfidenceAvg(0.95);
    setStep('preview');
    
    trackParseOk({
      rows: sampleRows.length,
      sourceType: 'sample',
      watermark: false
    });
  };
  
  const handleShowSampleOutput = () => {
    sampleModal.onOpen();
  };
  
  const handleUploadSuccess = async (uploadId: string, filename: string, rowCount?: number) => {
    setUploadId(uploadId);
    setFilename(filename);
    setError(null);
    
    // Since upload now returns transactions, we can skip the processing step
    // In a real implementation, upload route would return parsed transactions
    // For now, generate sample preview data
    const samplePreviewRows = Array.from({ length: Math.min(rowCount || 8, 25) }, (_, i) => ({
      id: `${uploadId}_${i}`,
      date: '2024-10-01',
      description: 'Sample Transaction',
      amount: -10.00,
      category: 'Uncategorized',
      confidence: 0.85
    }));
    
    setPreviewRows(samplePreviewRows);
    setTotalRows(rowCount || 0);
    setCategoriesCount(5);
    setConfidenceAvg(0.85);
    setStep('preview');
    
    trackUploadStarted({
      upload_id: uploadId,
      ext: filename.split('.').pop()?.toLowerCase(),
      consentTraining
    });
    
    trackParseOk({
      rows: rowCount || 0,
      sourceType: filename.split('.').pop()?.toLowerCase(),
      watermark: (rowCount || 0) > config.maxRows
    });
    
    trackPreviewViewed({
      rows: rowCount || 0,
      watermark: (rowCount || 0) > config.maxRows
    });
  };

  const handleUploadError = (errorMessage: string) => {
    setError('GENERIC_ERROR');
    setErrorContext({ message: errorMessage });
    setStep('upload');
  };

  const handleContinueToEmail = async (feedback?: Record<string, string>) => {
    // Save feedback if provided
    if (feedback && Object.keys(feedback).length > 0) {
      await handleFeedbackCollected(feedback);
    }
    
    // Check if email gate is enabled
    if (config.enableEmailGate) {
      setStep('email');
    } else {
      // Skip directly to download
      setStep('download');
    }
  };

  const handleFeedbackCollected = async (feedback: Record<string, string>) => {
    if (Object.keys(feedback).length > 0) {
      try {
        await saveFeedback(uploadId, feedback, previewRows);
        console.log(`[FEEDBACK] Saved ${Object.keys(feedback).length} feedback entries`);
      } catch (error) {
        console.error('[FEEDBACK] Failed to save:', error);
      }
    }
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!email || !email.includes('@')) {
      setError('EMAIL_INVALID');
      return;
    }
    
    trackVerifyClicked({ upload_id: uploadId, rows: totalRows });
    
    // Send verification code
    const result = await sendVerificationCode(email);
    
    if (!result.success) {
      setError((result.code as ErrorCode) || 'GENERIC_ERROR');
      return;
    }
    
    setStep('verify');
  };

  const handleBypassEmail = () => {
    setBypassedEmail(true);
    setStep('download');
    
    trackDownloadClicked({
      upload_id: uploadId,
      rows: totalRows,
      gate: 'bypass'
    });
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!verificationCode || verificationCode.length !== 6) {
      setError('CODE_EXPIRED');
      return;
    }
    
    const result = await verifyEmailCode(email, verificationCode);
    
    if (!result.success) {
      setError((result.code as ErrorCode) || 'TOKEN_INVALID');
      return;
    }
    
    // Track lead submission
    trackLeadSubmitted({
      source: 'free_categorizer',
      upload_id: uploadId,
      rows: totalRows
    });
    
    setStep('download');
  };

  const handleDownload = async () => {
    setError(null);
    
    const result = await exportCategorizedCSV(uploadId);
    
    if (!result.success) {
      setError((result.code as ErrorCode) || 'GENERIC_ERROR');
      return;
    }
    
    trackDownloadClicked({
      upload_id: uploadId,
      rows: Math.min(totalRows, config.maxRows),
      gate: bypassedEmail ? 'bypass' : 'email'
    });
    
    // Download CSV
    const blob = new Blob([result.csvData || ''], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.filename || 'categorized.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setStep('complete');
    setShowUpgradeModal(true);
  };

  const handleDelete = async () => {
    try {
      await deleteUpload(uploadId);
      
      trackDeleteClicked({ upload_id: uploadId });
      
      // Reset to upload step
      setUploadId('');
      setFilename('');
      setPreviewRows([]);
      setTotalRows(0);
      setStep('upload');
      setError(null);
      deleteModal.onClose();
      
      // Show confirmation (could use a toast here)
      alert('Upload deleted successfully');
    } catch (err) {
      setError('GENERIC_ERROR');
      deleteModal.onClose();
    }
  };

  const handleUpgradeClick = () => {
    trackUpgradeClicked({
      upload_id: uploadId,
      cta_location: 'post_export_modal'
    });
    
    window.open('/pricing?utm_source=free_tool&utm_medium=modal&utm_campaign=post_export', '_blank');
  };
  
  // Get error details if error exists
  const errorDetails = error ? getErrorDetails(error, errorContext) : null;
  
  const isWatermarked = totalRows > config.maxRows;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Free Bank Transaction Categorizer (CSV, OFX, QFX)
          </h1>
          <p className="text-xl text-gray-700 mb-6">
            Upload. Auto-categorize. Verify. Download CSV or export to QuickBooks.
          </p>
          <div className="flex flex-wrap justify-center items-center gap-3 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Uploads deleted within 24 hours</span>
            </div>
            <span className="text-gray-400">•</span>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Opt-in training only</span>
            </div>
            <span className="text-gray-400">•</span>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>SOC 2-aligned controls</span>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex justify-between items-center">
            {[
              { key: 'upload', label: 'Upload', icon: '📤' },
              { key: 'preview', label: 'Preview', icon: '👀' },
              { key: 'email', label: 'Verify', icon: '✉️' },
              { key: 'download', label: 'Download', icon: '⬇️' }
            ].map((s, idx) => {
              const isActive = ['upload', 'processing'].includes(step) && s.key === 'upload' ||
                              step === s.key ||
                              (step === 'verify' && s.key === 'email') ||
                              (step === 'complete' && s.key === 'download');
              const isComplete = 
                (step === 'preview' || step === 'email' || step === 'verify' || step === 'download' || step === 'complete') && s.key === 'upload' ||
                (step === 'email' || step === 'verify' || step === 'download' || step === 'complete') && s.key === 'preview' ||
                (step === 'download' || step === 'complete') && s.key === 'email' ||
                step === 'complete' && s.key === 'download';
              
              return (
                <div key={s.key} className="flex-1 flex items-center">
                  <div className="flex flex-col items-center flex-1">
                    <div 
                      className={`
                        w-12 h-12 rounded-full flex items-center justify-center text-xl
                        ${isComplete ? 'bg-green-500 text-white' : isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                      `}
                      role="status"
                      aria-label={`Step ${idx + 1}: ${s.label} - ${isComplete ? 'completed' : isActive ? 'current' : 'pending'}`}
                    >
                      {isComplete ? '✓' : s.icon}
                    </div>
                    <div className="mt-2 text-sm font-medium text-gray-700">{s.label}</div>
                  </div>
                  {idx < 3 && (
                    <div className={`flex-1 h-1 ${isComplete ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Error Alert with Repair Tips */}
        {errorDetails && (
          <div className="max-w-4xl mx-auto mb-6">
            <ErrorAlert error={errorDetails} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Step Content */}
        <div className="max-w-6xl mx-auto">
          {step === 'upload' && (
            <div className="space-y-6">
              <FreeDropzone
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                consentTraining={consentTraining}
              />
              
              {/* Consent Checkbox */}
              <div className="max-w-2xl mx-auto bg-white rounded-lg p-6 border border-gray-200">
                <Checkbox
                  isSelected={consentTraining}
                  onValueChange={setConsentTraining}
                  aria-label="Consent to use anonymized data for model training"
                >
                  <span className="text-sm text-gray-700">
                    Allow anonymized data to improve models (optional).{' '}
                    <Link href="/privacy" className="text-blue-600 hover:underline" target="_blank">
                      Privacy Policy
                    </Link>
                    {' • '}
                    <Link href="/dpa" className="text-blue-600 hover:underline" target="_blank">
                      DPA
                    </Link>
                  </span>
                </Checkbox>
                <p className="text-xs text-gray-500 mt-2 ml-7">
                  Your data is never used for training without your explicit consent.
                </p>
              </div>
              
              {/* Sample Actions */}
              <div className="flex justify-center gap-4">
                <Button
                  color="default"
                  variant="bordered"
                  onPress={handleSampleClick}
                  aria-label="Use sample bank statement"
                >
                  📊 Use Sample Statement
                </Button>
                <Button
                  color="default"
                  variant="bordered"
                  onPress={handleShowSampleOutput}
                  aria-label="View sample CSV output"
                >
                  👁️ See Sample CSV Output
                </Button>
              </div>
            </div>
          )}

          {step === 'processing' && (
            <div className="text-center py-20" role="status" aria-live="polite">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4" />
              <p className="text-xl font-medium text-gray-700">Processing your statement...</p>
              <p className="text-sm text-gray-500 mt-2">This usually takes 5-10 seconds</p>
            </div>
          )}

          {step === 'preview' && (
            <div className="space-y-6">
              {/* Watermark Banner */}
              {isWatermarked && (
                <Card className="border-2 border-yellow-300 bg-yellow-50">
                  <CardBody className="p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span className="text-yellow-600 text-xl">⚠️</span>
                        <div className="text-sm">
                          <p className="font-semibold text-yellow-900">
                            File has {totalRows} rows. Free tier limited to {config.maxRows} rows.
                          </p>
                          <p className="text-yellow-800">
                            Output will be watermarked and capped at {config.maxRows} rows.
                          </p>
                        </div>
                      </div>
                      <Button
                        as={Link}
                        href="/pricing"
                        color="warning"
                        size="sm"
                        onClick={() => trackUpgradeClicked({ upload_id: uploadId, cta_location: 'watermark_banner' })}
                      >
                        Remove Watermark → Upgrade
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              )}
              
              <ResultsPreview
                uploadId={uploadId}
                previewRows={previewRows}
                totalRows={totalRows}
                categoriesCount={categoriesCount}
                confidenceAvg={confidenceAvg}
                onContinue={handleContinueToEmail}
                onFeedbackCollected={handleFeedbackCollected}
              />
              
              {/* Delete Button */}
              <div className="flex justify-center">
                <Button
                  color="danger"
                  variant="light"
                  size="sm"
                  onPress={deleteModal.onOpen}
                  aria-label="Delete uploaded data immediately"
                >
                  🗑️ Delete Now
                </Button>
              </div>
            </div>
          )}

          {step === 'email' && (
            <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Almost There!</h2>
              <p className="text-gray-600 mb-6">
                Enter your email to receive a verification code and download your categorized CSV.
              </p>
              
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email-input" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    id="email-input"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@example.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                    aria-required="true"
                    aria-label="Email address for verification"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Email Me the CSV
                </button>
              </form>
              
              {/* Bypass Option */}
              <div className="text-center mt-4">
                <button
                  onClick={handleBypassEmail}
                  className="text-sm text-gray-600 hover:text-gray-900 underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-2 py-1"
                  aria-label="Skip email verification and download directly"
                >
                  Skip for now
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-4 text-center">
                We respect your privacy. See our{' '}
                <Link href="/privacy" className="text-blue-600 hover:underline">
                  Privacy Policy
                </Link>
                .
              </p>
            </div>
          )}

          {step === 'verify' && (
            <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Check Your Email!</h2>
              <p className="text-gray-600 mb-6">
                We sent a 6-digit code to <strong>{email}</strong>. Enter it below to download your CSV.
              </p>
              
              <form onSubmit={handleVerifySubmit} className="space-y-4">
                <div>
                  <label htmlFor="code-input" className="block text-sm font-medium text-gray-700 mb-2">
                    Verification Code
                  </label>
                  <input
                    id="code-input"
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    maxLength={6}
                    className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 tracking-widest"
                    required
                    aria-required="true"
                    aria-label="6-digit verification code"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Verify & Download
                </button>
              </form>
              
              <button
                onClick={() => sendVerificationCode(email)}
                className="w-full mt-4 text-sm text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-2 py-1"
              >
                Didn't receive it? Resend code
              </button>
            </div>
          )}

          {step === 'download' && (
            <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {bypassedEmail ? 'Ready to Download!' : 'Email Verified!'}
              </h2>
              <p className="text-gray-600 mb-6">
                Your categorized CSV is ready to download.
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={handleDownload}
                  className="w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors text-lg focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                  aria-label="Download categorized CSV file"
                >
                  📥 Download CSV
                </button>
                
                <button
                  onClick={() => {
                    trackUpgradeClicked({ source: 'qbo_export', upload_id: uploadId });
                    qboModal.onOpen();
                  }}
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-lg focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label="Export to QuickBooks Online"
                >
                  🚀 Export to QuickBooks
                </button>
              </div>
              
              <p className="text-sm text-gray-500 mt-4">
                {Math.min(totalRows, config.maxRows)} rows • {categoriesCount} categories • {(confidenceAvg * 100).toFixed(0)}% avg confidence
              </p>
            </div>
          )}
        </div>

        {/* Footer Compliance Text */}
        <div className="mt-16 text-center space-y-4">
          <p className="text-sm text-gray-600">
            <span className="font-semibold">Free tier limits:</span> {config.maxRows} rows, watermarked output.{' '}
            <Link href="/pricing" className="text-blue-600 hover:underline">
              Upgrade for unlimited rows →
            </Link>
          </p>
          <p className="text-xs text-gray-500">
            Uploads deleted within 24 hours. We do not use free-tool data for model training unless you opt in at upload.
            This is not financial advice.
          </p>
        </div>
      </div>

      {/* Sample Output Modal */}
      <Modal isOpen={sampleModal.isOpen} onClose={sampleModal.onClose} size="2xl">
        <ModalContent>
          <ModalHeader>Sample CSV Output</ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Here's what your categorized output will look like:
              </p>
              
              <div className="border rounded-lg overflow-auto max-h-80">
                <table className="w-full text-xs">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-left">Description</th>
                      <th className="px-3 py-2 text-right">Amount</th>
                      <th className="px-3 py-2 text-left">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SAMPLE_CSV_DATA.split('\n').slice(1).map((line, idx) => {
                      const [date, description, amount, category] = line.split(',');
                      return (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{date}</td>
                          <td className="px-3 py-2">{description}</td>
                          <td className="px-3 py-2 text-right">{amount}</td>
                          <td className="px-3 py-2">{category}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              <div className="text-center">
                <Button
                  color="primary"
                  onPress={() => {
                    const blob = new Blob([SAMPLE_CSV_DATA], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sample_output.csv';
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Download Sample CSV
                </Button>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={sampleModal.onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={deleteModal.isOpen} onClose={deleteModal.onClose}>
        <ModalContent>
          <ModalHeader>Delete Upload?</ModalHeader>
          <ModalBody>
            <p className="text-gray-700">
              This will permanently delete your uploaded file and all processed data.
              This action cannot be undone.
            </p>
          </ModalBody>
          <ModalFooter>
            <Button variant="light" onPress={deleteModal.onClose}>
              Cancel
            </Button>
            <Button color="danger" onPress={handleDelete}>
              Delete Now
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* QuickBooks Export Modal */}
      <Modal isOpen={qboModal.isOpen} onClose={qboModal.onClose} size="lg">
        <ModalContent>
          <ModalHeader className="flex flex-col gap-1">
            <span className="text-2xl">🚀 QuickBooks Online Export</span>
          </ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <p className="text-gray-700">
                <strong>Direct QuickBooks Online integration</strong> is available on paid plans.
              </p>
              
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  What you get with an account:
                </h4>
                <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 flex-shrink-0">✓</span>
                    <span>Direct QuickBooks Online & Xero integration</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 flex-shrink-0">✓</span>
                    <span>Automatic journal entry creation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 flex-shrink-0">✓</span>
                    <span>Custom categorization rules</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 flex-shrink-0">✓</span>
                    <span>Unlimited transactions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 flex-shrink-0">✓</span>
                    <span>Priority support</span>
                  </li>
                </ul>
              </div>
              
              <p className="text-sm text-gray-600">
                <strong>For now:</strong> Download your categorized CSV above and manually import it into QuickBooks.
              </p>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button color="default" variant="light" onPress={qboModal.onClose}>
              Close
            </Button>
            <Button 
              color="primary" 
              onPress={() => {
                qboModal.onClose();
                window.location.href = '/pricing';
              }}
            >
              View Pricing
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="upgrade-modal-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8">
            <h2 id="upgrade-modal-title" className="text-2xl font-bold text-gray-900 mb-4">
              🎉 Download Complete!
            </h2>
            <p className="text-gray-600 mb-6">
              Your free CSV includes the first {config.maxRows} rows. Want more?
            </p>
            
            <div className="space-y-2 mb-6">
              {[
                'Unlimited rows',
                'Export to QuickBooks/Xero',
                'Advanced categorization rules',
                'Priority support'
              ].map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-green-600">✅</span>
                  <span>{feature}</span>
                </div>
              ))}
            </div>
            
            <div className="space-y-3">
              <button
                onClick={handleUpgradeClick}
                className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                View Pricing Plans
              </button>
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="w-full py-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded"
              >
                No Thanks
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Rich Content Section for SEO */}
      <FreeCategorizerContent />
    </div>
  );
}

