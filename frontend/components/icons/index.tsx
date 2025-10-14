// Shared SVG Icon Components with Green-Blue Gradients

export const AIIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#06b6d4" />
      </linearGradient>
    </defs>
    <rect x="3" y="4" width="18" height="12" rx="2" fill="url(#aiGradient)" />
    <rect x="5" y="7" width="14" height="6" rx="1" fill="white" opacity="0.9" />
    <circle cx="8" cy="10" r="1" fill="url(#aiGradient)" />
    <circle cx="16" cy="10" r="1" fill="url(#aiGradient)" />
    <path d="M8 12h8" stroke="url(#aiGradient)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="searchGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <circle cx="11" cy="11" r="8" fill="url(#searchGradient)" />
    <path d="m21 21-4.35-4.35" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <circle cx="11" cy="11" r="3" fill="white" opacity="0.8" />
  </svg>
);

export const AutomationIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="autoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06b6d4" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="url(#autoGradient)" />
    <circle cx="12" cy="12" r="2" fill="white" opacity="0.9" />
  </svg>
);

export const AnalyticsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="analyticsGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
    </defs>
    <rect x="3" y="16" width="4" height="5" rx="1" fill="url(#analyticsGradient)" />
    <rect x="8" y="12" width="4" height="9" rx="1" fill="url(#analyticsGradient)" />
    <rect x="13" y="8" width="4" height="13" rx="1" fill="url(#analyticsGradient)" />
    <rect x="18" y="4" width="4" height="17" rx="1" fill="url(#analyticsGradient)" />
    <path d="M5 16h14" stroke="white" strokeWidth="1" opacity="0.6" />
  </svg>
);

export const SecurityIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="securityGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <path d="M12 2l8 4v6c0 5.55-3.84 10.74-9 12-5.16-1.26-9-6.45-9-12V6l8-4z" fill="url(#securityGradient)" />
    <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const IntegrationIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="integrationGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#0891b2" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <rect x="2" y="6" width="20" height="12" rx="2" fill="url(#integrationGradient)" />
    <circle cx="8" cy="12" r="2" fill="white" opacity="0.9" />
    <circle cx="16" cy="12" r="2" fill="white" opacity="0.9" />
    <path d="M10 12h4" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M3 9h3M3 15h3M18 9h3M18 15h3" stroke="white" strokeWidth="1" opacity="0.6" />
  </svg>
);

export const DashboardIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="dashboardGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#06b6d4" />
      </linearGradient>
    </defs>
    <rect x="3" y="3" width="7" height="7" rx="1" fill="url(#dashboardGradient)" />
    <rect x="14" y="3" width="7" height="7" rx="1" fill="url(#dashboardGradient)" />
    <rect x="3" y="14" width="7" height="7" rx="1" fill="url(#dashboardGradient)" />
    <rect x="14" y="14" width="7" height="7" rx="1" fill="url(#dashboardGradient)" />
  </svg>
);

export const TransactionIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="transactionGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="url(#transactionGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const VendorIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="vendorGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06b6d4" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" fill="url(#vendorGradient)" />
    <polyline points="9,22 9,12 15,12 15,22" fill="white" opacity="0.9" />
  </svg>
);

export const SettingsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="settingsGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#0891b2" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <circle cx="12" cy="12" r="3" fill="url(#settingsGradient)" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="url(#settingsGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const ReceiptIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="receiptGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
    </defs>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="url(#receiptGradient)" />
    <polyline points="14,2 14,8 20,8" fill="white" opacity="0.9" />
    <line x1="16" y1="13" x2="8" y2="13" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <line x1="16" y1="17" x2="8" y2="17" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <polyline points="10,9 9,9 8,9" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const RulesIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="rulesGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#06b6d4" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <path d="M9 12l2 2 4-4" stroke="url(#rulesGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3" fill="url(#rulesGradient)" />
    <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3" fill="url(#rulesGradient)" />
    <path d="M12 3c0 1-1 3-3 3s-3-2-3-3 1-3 3-3 3 2 3 3" fill="url(#rulesGradient)" />
    <path d="M12 21c0-1 1-3 3-3s3 2 3 3-1 3-3 3-3-2-3-3" fill="url(#rulesGradient)" />
  </svg>
);

export const AuditIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="auditGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#059669" />
        <stop offset="100%" stopColor="#0891b2" />
      </linearGradient>
    </defs>
    <path d="M9 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2h-4" stroke="url(#auditGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <rect x="9" y="11" width="6" height="11" rx="1" fill="url(#auditGradient)" />
    <path d="M9 7v4M15 7v4M9 11h6" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const ExportIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
    <defs>
      <linearGradient id="exportGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#0891b2" />
        <stop offset="100%" stopColor="#0284c7" />
      </linearGradient>
    </defs>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="url(#exportGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <polyline points="7,10 12,15 17,10" stroke="url(#exportGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="12" y1="15" x2="12" y2="3" stroke="url(#exportGradient)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);
