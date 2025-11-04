'use client';

/**
 * Free Categorizer Page
 * 
 * Main page for the free statement categorizer tool.
 * Implements multi-step flow: Upload → Preview → Email → Download
 */

import React, { useState, useEffect } from 'react';
import { FreeDropzone } from '@/components/FreeDropzone';
import { ResultsPreview } from '@/components/ResultsPreview';
import { proposeCategorization, sendVerificationCode, verifyEmailCode, exportCategorizedCSV, saveFeedback } from './actions';
import { trackEmailSubmit, trackEmailVerified, trackExportSuccess, trackUpgradeClick, storeUTMParams } from '@/lib/telemetry';

type Step = 'upload' | 'processing' | 'preview' | 'email' | 'verify' | 'download' | 'complete';

export default function FreeCategorizerPage() {
  const [step, setStep] = useState<Step>('upload');
  const [uploadId, setUploadId] = useState<string>('');
  const [filename, setFilename] = useState<string>('');
  const [previewRows, setPreviewRows] = useState<any[]>([]);
  const [totalRows, setTotalRows] = useState<number>(0);
  const [categoriesCount, setCategoriesCount] = useState<number>(0);
  const [confidenceAvg, setConfidenceAvg] = useState<number>(0);
  const [email, setEmail] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  // Store UTM params on mount
  useEffect(() => {
    storeUTMParams();
  }, []);

  const handleUploadSuccess = async (uploadId: string, filename: string) => {
    setUploadId(uploadId);
    setFilename(filename);
    setStep('processing');
    setError('');
    
    // Call propose categorization
    const result = await proposeCategorization(uploadId);
    
    if (!result.success) {
      setError(result.error || 'Categorization failed');
      setStep('upload');
      return;
    }
    
    setPreviewRows(result.previewRows || []);
    setTotalRows(result.totalRows || 0);
    setCategoriesCount(result.categoriesCount || 0);
    setConfidenceAvg(result.confidenceAvg || 0);
    setStep('preview');
  };

  const handleUploadError = (error: string) => {
    setError(error);
    setStep('upload');
  };

  const handleContinueToEmail = () => {
    setStep('email');
  };

  const handleFeedbackCollected = async (feedback: Record<string, string>) => {
    // Save feedback for training
    if (Object.keys(feedback).length > 0) {
      try {
        await saveFeedback(uploadId, feedback, previewRows);
        console.log(`[FEEDBACK] Saved ${Object.keys(feedback).length} feedback entries`);
      } catch (error) {
        console.error('[FEEDBACK] Failed to save:', error);
        // Don't block the user flow if feedback save fails
      }
    }
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    
    // Track email submit
    trackEmailSubmit({
      upload_id: uploadId,
      email_domain: email.split('@')[1]
    });
    
    // Send verification code
    const result = await sendVerificationCode(email);
    
    if (!result.success) {
      setError(result.error || 'Failed to send code');
      return;
    }
    
    setStep('verify');
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter the 6-digit code');
      return;
    }
    
    const startTime = Date.now();
    
    // Verify code
    const result = await verifyEmailCode(email, verificationCode);
    
    if (!result.success) {
      setError(result.error || 'Invalid code');
      return;
    }
    
    // Track verification
    trackEmailVerified({
      upload_id: uploadId,
      verification_ms: Date.now() - startTime
    });
    
    setStep('download');
  };

  const handleDownload = async () => {
    setError('');
    
    // Export CSV
    const result = await exportCategorizedCSV(uploadId);
    
    if (!result.success) {
      setError(result.error || 'Export failed');
      return;
    }
    
    // Track export
    trackExportSuccess({
      upload_id: uploadId,
      rows_exported: Math.min(totalRows, 500),
      categories_count: categoriesCount
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

  const handleUpgradeClick = () => {
    trackUpgradeClick({
      upload_id: uploadId,
      cta_location: 'post_export_modal'
    });
    
    window.open('/pricing?utm_source=free_tool&utm_medium=modal&utm_campaign=post_export', '_blank');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Turn Your Bank Statement Into a Categorized CSV
          </h1>
          <div className="flex flex-col md:flex-row justify-center items-center gap-4 text-lg text-gray-700">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🚀</span>
              <span>Upload any format</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🤖</span>
              <span>AI categorizes instantly</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">📊</span>
              <span>Export in seconds</span>
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
                    <div className={`
                      w-12 h-12 rounded-full flex items-center justify-center text-xl
                      ${isComplete ? 'bg-green-500 text-white' : isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                    `}>
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

        {/* Error Alert */}
        {error && (
          <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <span className="text-red-600 text-xl">⚠️</span>
                <p className="text-red-800 font-medium">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Step Content */}
        <div className="max-w-6xl mx-auto">
          {step === 'upload' && (
            <FreeDropzone
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          )}

          {step === 'processing' && (
            <div className="text-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4" />
              <p className="text-xl font-medium text-gray-700">Processing your statement...</p>
              <p className="text-sm text-gray-500 mt-2">This usually takes 5-10 seconds</p>
            </div>
          )}

          {step === 'preview' && (
            <ResultsPreview
              uploadId={uploadId}
              previewRows={previewRows}
              totalRows={totalRows}
              categoriesCount={categoriesCount}
              confidenceAvg={confidenceAvg}
              onContinue={handleContinueToEmail}
              onFeedbackCollected={handleFeedbackCollected}
            />
          )}

          {step === 'email' && (
            <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Almost There!</h2>
              <p className="text-gray-600 mb-6">
                Enter your email to receive a verification code and download your categorized CSV.
              </p>
              
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@example.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Send Verification Code
                </button>
              </form>
              
              <p className="text-xs text-gray-500 mt-4 text-center">
                We respect your privacy. See our <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a>.
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Verification Code
                  </label>
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    maxLength={6}
                    className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 tracking-widest"
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Verify & Download
                </button>
              </form>
              
              <button
                onClick={() => sendVerificationCode(email)}
                className="w-full mt-4 text-sm text-blue-600 hover:underline"
              >
                Didn't receive it? Resend code
              </button>
            </div>
          )}

          {step === 'download' && (
            <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Email Verified!</h2>
              <p className="text-gray-600 mb-6">
                Your categorized CSV is ready to download.
              </p>
              
              <button
                onClick={handleDownload}
                className="w-full py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors text-lg"
              >
                📥 Download CSV
              </button>
              
              <p className="text-sm text-gray-500 mt-4">
                {Math.min(totalRows, 500)} rows • {categoriesCount} categories • {(confidenceAvg * 100).toFixed(0)}% avg confidence
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-16 text-center space-y-4">
          <p className="text-sm text-gray-600">
            <span className="font-semibold">Free tier limits:</span> 500 rows, watermarked output.{' '}
            <a href="/pricing" className="text-blue-600 hover:underline">Upgrade for unlimited rows →</a>
          </p>
          <p className="text-xs text-gray-500">
            Files are automatically deleted after 24 hours. We never store your banking credentials.
          </p>
          <p className="text-xs text-gray-400">
            Not financial advice. This tool provides categorization suggestions only.
          </p>
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🎉 Download Complete!</h2>
            <p className="text-gray-600 mb-6">
              Your free CSV includes the first 500 rows. Want more?
            </p>
            
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="text-green-600">✅</span>
                <span>Unlimited rows</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="text-green-600">✅</span>
                <span>Export to QuickBooks/Xero</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="text-green-600">✅</span>
                <span>Advanced categorization rules</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="text-green-600">✅</span>
                <span>Priority support</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={handleUpgradeClick}
                className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Pricing Plans
              </button>
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="w-full py-2 text-gray-600 hover:text-gray-900"
              >
                No Thanks
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

