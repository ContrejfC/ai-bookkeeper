'use client';

/**
 * FreeDropzone Component
 * 
 * Drag-and-drop file upload component for the free categorizer tool.
 * Handles file validation, CAPTCHA, and upload progress.
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { trackUploadStart, trackUploadSuccess, trackUploadFail } from '@/lib/telemetry';

interface FreeDropzoneProps {
  onUploadSuccess: (uploadId: string, filename: string, rowCount?: number) => void;
  onUploadError: (error: string) => void;
  disabled?: boolean;
}

export function FreeDropzone({ onUploadSuccess, onUploadError, disabled }: FreeDropzoneProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    
    // Track upload start
    trackUploadStart({
      file_type: file.name.split('.').pop()?.toLowerCase(),
      file_size: file.size,
      mime_type: file.type
    });
    
    setUploading(true);
    setProgress(10);
    
    try {
      // Get CAPTCHA token
      if (!captchaToken) {
        const token = await getCaptchaToken();
        setCaptchaToken(token);
      }
      
      setProgress(20);
      
      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('captcha_token', captchaToken || '');
      
      // Add UTM params from session
      const utmParams = getUTMParams();
      if (utmParams.utm_source) formData.append('utm_source', utmParams.utm_source);
      if (utmParams.utm_medium) formData.append('utm_medium', utmParams.utm_medium);
      if (utmParams.utm_campaign) formData.append('utm_campaign', utmParams.utm_campaign);
      
      setProgress(40);
      
      const response = await fetch('/api/free/upload', {
        method: 'POST',
        body: formData
      });
      
      setProgress(70);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }
      
      const result = await response.json();
      
      setProgress(100);
      
      // Track success
      trackUploadSuccess({
        upload_id: result.upload_id,
        file_type: file.name.split('.').pop()?.toLowerCase(),
        file_size: file.size
      });
      
      // Notify parent
      onUploadSuccess(result.upload_id, result.filename);
      
    } catch (error) {
      console.error('Upload error:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      // Track failure
      trackUploadFail({
        file_type: file.name.split('.').pop()?.toLowerCase(),
        error_message: errorMessage
      });
      
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [captchaToken, onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/x-ofx': ['.ofx'],
      'application/vnd.intu.qfx': ['.qfx'],
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/zip': ['.zip']
    },
    maxFiles: 1,
    maxSize: 200 * 1024 * 1024, // 200 MB
    disabled: disabled || uploading
  });

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
            <p className="text-lg font-medium text-gray-700">
              Uploading... {progress}%
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2 max-w-md mx-auto">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <svg
              className="mx-auto h-16 w-16 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            
            <div>
              <p className="text-xl font-semibold text-gray-900">
                {isDragActive ? 'Drop your file here' : 'Drag & drop your bank statement'}
              </p>
              <p className="mt-2 text-sm text-gray-600">
                or click to browse
              </p>
            </div>
            
            <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
              <span className="px-2 py-1 bg-gray-100 rounded">CSV</span>
              <span className="px-2 py-1 bg-gray-100 rounded">OFX</span>
              <span className="px-2 py-1 bg-gray-100 rounded">QFX</span>
              <span className="px-2 py-1 bg-gray-100 rounded">PDF</span>
              <span className="px-2 py-1 bg-gray-100 rounded">JPG</span>
              <span className="px-2 py-1 bg-gray-100 rounded">PNG</span>
              <span className="px-2 py-1 bg-gray-100 rounded">ZIP</span>
            </div>
            
            <p className="text-xs text-gray-500 mt-4">
              Max 500 rows • Files auto-delete after 24h • No credit card required
            </p>
          </div>
        )}
      </div>
      
      {fileRejections.length > 0 && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-800">File rejected:</p>
          <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
            {fileRejections.map(({ file, errors }) => (
              <li key={file.name}>
                {file.name}: {errors.map(e => e.message).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Turnstile CAPTCHA Widget */}
      <div
        id="turnstile-widget"
        className="mt-4 flex justify-center"
        data-sitekey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY}
        data-callback="onTurnstileSuccess"
      />
    </div>
  );
}

// Helper: Get CAPTCHA token
async function getCaptchaToken(): Promise<string> {
  return new Promise((resolve) => {
    // Turnstile callback
    (window as any).onTurnstileSuccess = (token: string) => {
      resolve(token);
    };
    
    // Load Turnstile if not already loaded
    if (!(window as any).turnstile) {
      const script = document.createElement('script');
      script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
      script.async = true;
      document.head.appendChild(script);
    }
  });
}

// Helper: Get UTM params from session
function getUTMParams(): {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
} {
  if (typeof window === 'undefined') return {};
  
  try {
    const stored = sessionStorage.getItem('utm_params');
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

