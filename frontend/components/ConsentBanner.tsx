'use client';

import React, { useState, useEffect } from 'react';

interface ConsentBannerProps {
  onAccept: () => void;
  onDecline: () => void;
}

export function ConsentBanner({ onAccept, onDecline }: ConsentBannerProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Check if user has already consented
    const consent = localStorage.getItem('analytics_consent');
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('analytics_consent', 'accepted');
    localStorage.setItem('analytics_consent_date', new Date().toISOString());
    setVisible(false);
    onAccept();
  };

  const handleDecline = () => {
    localStorage.setItem('analytics_consent', 'declined');
    setVisible(false);
    onDecline();
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-6 shadow-2xl z-50 border-t-4 border-blue-500">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex-1">
          <h3 className="font-semibold text-lg mb-2">🍪 We Value Your Privacy</h3>
          <p className="text-sm text-gray-300">
            We use cookies and analytics to improve your experience. By accepting, you agree to our use of Google Analytics and advertising cookies. 
            <a href="/privacy" className="underline ml-1">Privacy Policy</a>
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleDecline}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
          >
            Decline
          </button>
          <button
            onClick={handleAccept}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Accept All
          </button>
        </div>
      </div>
    </div>
  );
}

