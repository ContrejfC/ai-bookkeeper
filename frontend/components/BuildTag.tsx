/**
 * Build Tag Debug Ribbon
 * ======================
 * 
 * Shows build info when ?verify=1 query param is set.
 * Useful for verifying deployment in production.
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export function BuildTag() {
  const searchParams = useSearchParams();
  const [showTag, setShowTag] = useState(false);
  
  useEffect(() => {
    setShowTag(searchParams.get('verify') === '1' || process.env.NODE_ENV !== 'production');
  }, [searchParams]);
  
  if (!showTag) return null;
  
  const commitSha = process.env.NEXT_PUBLIC_COMMIT_SHA || 
                    process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA || 
                    'unknown';
  const shortSha = commitSha.slice(0, 7);
  const env = process.env.NEXT_PUBLIC_VERCEL_ENV || 'local';
  
  return (
    <div
      id="__build_tag"
      style={{
        position: 'fixed',
        bottom: 8,
        right: 8,
        opacity: 0.8,
        fontSize: 12,
        padding: '4px 8px',
        border: '1px solid #ccc',
        borderRadius: 6,
        background: '#fff',
        color: '#333',
        zIndex: 99999,
        fontFamily: 'monospace',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}
    >
      <span>sha: {shortSha}</span>
      <span style={{ margin: '0 8px', opacity: 0.5 }}>•</span>
      <span>env: {env}</span>
    </div>
  );
}

