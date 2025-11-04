/**
 * Free Tool Telemetry
 * 
 * Tracks conversion funnel events for the free statement categorizer.
 * Integrates with PostHog or custom analytics backend.
 */

import { getFreeToolConfig } from './validators';

// PostHog client (browser-side)
declare global {
  interface Window {
    posthog?: any;
  }
}

export type TelemetryEvent =
  | 'free_upload_start'
  | 'free_upload_ok'
  | 'free_upload_fail'
  | 'free_propose_ok'
  | 'free_propose_fail'
  | 'free_preview_view'
  | 'free_email_submit'
  | 'free_email_verified'
  | 'free_export_ok'
  | 'free_export_fail'
  | 'cta_upgrade_click';

export interface TelemetryProperties {
  // File properties
  file_type?: string;
  file_size?: number;
  mime_type?: string;
  
  // Processing properties
  upload_id?: string;
  rows_total?: number;
  rows_exported?: number;
  categories_count?: number;
  confidence_avg?: number;
  parse_ms?: number;
  verification_ms?: number;
  
  // UTM tracking
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  
  // User properties
  email_domain?: string;
  ip_geo?: string;
  user_agent?: string;
  
  // Error properties
  error_code?: string;
  error_message?: string;
  
  // CTA properties
  cta_location?: string;
  
  // Additional context
  [key: string]: any;
}

class Telemetry {
  private enabled: boolean;
  private config: any;
  
  constructor() {
    this.enabled = process.env.NODE_ENV === 'production' || process.env.NEXT_PUBLIC_ENABLE_TELEMETRY === 'true';
    this.config = getFreeToolConfig();
  }
  
  /**
   * Track an event
   */
  track(event: TelemetryEvent, properties: TelemetryProperties = {}): void {
    if (!this.enabled) {
      console.log('[Telemetry]', event, properties);
      return;
    }
    
    // Validate required properties based on config
    const requiredProps = this.config.telemetry?.required_properties || [];
    const missingProps = requiredProps.filter((prop: string) => !(prop in properties));
    
    if (missingProps.length > 0) {
      console.warn(`[Telemetry] Missing required properties for ${event}:`, missingProps);
    }
    
    // Add timestamp
    const enrichedProperties = {
      ...properties,
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV,
      tool: 'free_categorizer'
    };
    
    // Send to PostHog (browser-side)
    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.capture(event, enrichedProperties);
    }
    
    // Send to custom backend (optional)
    this.sendToBackend(event, enrichedProperties);
  }
  
  /**
   * Send event to custom analytics backend
   */
  private async sendToBackend(event: TelemetryEvent, properties: TelemetryProperties): Promise<void> {
    try {
      const endpoint = process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT;
      
      if (!endpoint) return;
      
      await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ event, properties }),
        // Don't wait for response
        keepalive: true
      }).catch(() => {
        // Silently fail - don't block user experience
      });
    } catch (error) {
      // Silently fail
    }
  }
  
  /**
   * Identify user (for email tracking)
   */
  identify(email: string, properties: Record<string, any> = {}): void {
    if (!this.enabled) return;
    
    // Hash email for privacy
    const emailDomain = email.split('@')[1];
    
    const userProperties = {
      ...properties,
      email_domain: emailDomain,
      identified_at: new Date().toISOString()
    };
    
    if (typeof window !== 'undefined' && window.posthog) {
      // Don't send raw email to PostHog
      window.posthog.identify(email, userProperties);
    }
  }
  
  /**
   * Track page view
   */
  pageView(path: string): void {
    if (!this.enabled) return;
    
    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.capture('$pageview', { path });
    }
  }
  
  /**
   * Set user properties
   */
  setUserProperties(properties: Record<string, any>): void {
    if (!this.enabled) return;
    
    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.people.set(properties);
    }
  }
}

// Singleton instance
export const telemetry = new Telemetry();

// Convenience functions

export function trackUploadStart(properties: TelemetryProperties): void {
  telemetry.track('free_upload_start', properties);
}

export function trackUploadSuccess(properties: TelemetryProperties): void {
  telemetry.track('free_upload_ok', properties);
}

export function trackUploadFail(properties: TelemetryProperties): void {
  telemetry.track('free_upload_fail', properties);
}

export function trackProposeSuccess(properties: TelemetryProperties): void {
  telemetry.track('free_propose_ok', properties);
}

export function trackProposeFail(properties: TelemetryProperties): void {
  telemetry.track('free_propose_fail', properties);
}

export function trackPreviewView(properties: TelemetryProperties): void {
  telemetry.track('free_preview_view', properties);
}

export function trackEmailSubmit(properties: TelemetryProperties): void {
  telemetry.track('free_email_submit', properties);
}

export function trackEmailVerified(properties: TelemetryProperties): void {
  telemetry.track('free_email_verified', properties);
}

export function trackExportSuccess(properties: TelemetryProperties): void {
  telemetry.track('free_export_ok', properties);
}

export function trackExportFail(properties: TelemetryProperties): void {
  telemetry.track('free_export_fail', properties);
}

export function trackUpgradeClick(properties: TelemetryProperties): void {
  telemetry.track('cta_upgrade_click', properties);
}

/**
 * Calculate conversion metrics
 */
export interface ConversionMetrics {
  upload_to_preview: number;
  preview_to_email: number;
  email_to_export: number;
  export_to_upgrade_click: number;
  overall_conversion: number;
}

export async function calculateConversionMetrics(
  startDate: Date,
  endDate: Date
): Promise<ConversionMetrics> {
  // This would query your analytics backend
  // Placeholder implementation
  return {
    upload_to_preview: 0.85,
    preview_to_email: 0.70,
    email_to_export: 0.90,
    export_to_upgrade_click: 0.05,
    overall_conversion: 0.05
  };
}

/**
 * Get coarse IP geolocation (country level only, privacy-safe)
 */
export async function getCoarseGeoLocation(): Promise<string | undefined> {
  try {
    // Use Cloudflare headers if available
    if (typeof window === 'undefined') {
      // Server-side: check request headers
      return undefined;
    }
    
    // Client-side: make request to get location
    const response = await fetch('https://ipapi.co/json/');
    const data = await response.json();
    return data.country_code; // Only country code, not city/precise location
  } catch (error) {
    return undefined;
  }
}

/**
 * Extract UTM parameters from URL
 */
export function extractUTMParams(): {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
} {
  if (typeof window === 'undefined') return {};
  
  const params = new URLSearchParams(window.location.search);
  
  return {
    utm_source: params.get('utm_source') || undefined,
    utm_medium: params.get('utm_medium') || undefined,
    utm_campaign: params.get('utm_campaign') || undefined
  };
}

/**
 * Store UTM parameters in session storage
 */
export function storeUTMParams(): void {
  if (typeof window === 'undefined') return;
  
  const params = extractUTMParams();
  
  if (Object.keys(params).length > 0) {
    sessionStorage.setItem('utm_params', JSON.stringify(params));
  }
}

/**
 * Retrieve stored UTM parameters
 */
export function getStoredUTMParams(): {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
} {
  if (typeof window === 'undefined') return {};
  
  const stored = sessionStorage.getItem('utm_params');
  
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return {};
    }
  }
  
  return {};
}



