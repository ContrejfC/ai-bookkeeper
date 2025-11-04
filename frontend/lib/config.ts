/**
 * Configuration for Free Tool - Trust, Compliance, and Conversion v1
 * =================================================================
 * 
 * Environment-driven configuration for the free categorizer tool.
 */

export interface FreeToolConfig {
  soc2Status: 'aligned' | 'in_progress' | 'certified';
  maxRows: number;
  maxFileMB: number;
  enableEmailGate: boolean;
  retentionHours: number;
  adminPurgeToken?: string;
}

/**
 * Get free tool configuration from environment variables
 */
export function getFreeToolConfig(): FreeToolConfig {
  return {
    soc2Status: (process.env.SOC2_STATUS as any) || 'aligned',
    maxRows: parseInt(process.env.FREE_MAX_ROWS || '500', 10),
    maxFileMB: parseInt(process.env.FREE_MAX_FILE_MB || '10', 10),
    enableEmailGate: process.env.NEXT_PUBLIC_ENABLE_EMAIL_GATE === 'true',
    retentionHours: parseInt(process.env.FREE_RETENTION_HOURS || '24', 10),
    adminPurgeToken: process.env.ADMIN_PURGE_TOKEN,
  };
}

/**
 * Get SOC2 status display text
 */
export function getSOC2StatusText(): string {
  const config = getFreeToolConfig();
  
  switch (config.soc2Status) {
    case 'certified':
      return 'SOC 2 Type II certified';
    case 'in_progress':
      return 'SOC 2 Type II in progress';
    case 'aligned':
    default:
      return 'SOC 2-aligned controls';
  }
}

/**
 * Format date for policy pages using America/New_York timezone
 */
export function formatPolicyDate(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  return dateObj.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'America/New_York'
  });
}

