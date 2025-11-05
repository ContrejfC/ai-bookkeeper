'use client';

/**
 * UploadZone Component
 * =====================
 * Drag-drop file upload for CSV/OFX/QFX
 */

import { useCallback, useState } from 'react';
import { getFlags } from '@/lib/flags';

interface UploadZoneProps {
  onFileSelected: (file: File) => void;
  acceptedFormats?: string[];
}

export function UploadZone({ onFileSelected, acceptedFormats = ['.csv', '.ofx', '.qfx'] }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const flags = getFlags();
  const maxSizeMB = flags.freeMaxFileMb;

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSelect(file);
    }
  }, []);

  const validateAndSelect = (file: File) => {
    // Check file size
    if (file.size > maxSizeMB * 1024 * 1024) {
      alert(`File too large. Maximum size is ${maxSizeMB}MB.`);
      return;
    }
    
    // Check file extension
    const ext = file.name.toLowerCase().match(/\.(csv|ofx|qfx|zip)$/)?.[1];
    if (!ext) {
      alert('Please upload a CSV, OFX, or QFX file.');
      return;
    }
    
    onFileSelected(file);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
        isDragging
          ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-emerald-400'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept={acceptedFormats.join(',')}
        onChange={handleFileInput}
      />
      
      <label htmlFor="file-upload" className="cursor-pointer">
        <div className="flex flex-col items-center gap-4">
          <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          
          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              Drop your file here or click to browse
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              CSV, OFX, or QFX • Up to {maxSizeMB}MB • Max {flags.freeMaxRows} rows
            </p>
          </div>
          
          <button
            type="button"
            className="px-6 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition"
          >
            Choose File
          </button>
        </div>
      </label>
    </div>
  );
}

