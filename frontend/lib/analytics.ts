/**
 * Analytics Wrapper - Provider-Agnostic Event Tracking
 * ====================================================
 * 
 * Unified interface for tracking conversion funnel events.
 * Supports GA4, PostHog, Amplitude, or no-op if not configured.
 */

type AnalyticsEvent =
  | 'free_categorizer_upload_started'
  | 'free_categorizer_upload_failed'
  | 'free_categorizer_parse_ok'
  | 'free_categorizer_preview_viewed'
  | 'free_categorizer_verify_clicked'
  | 'free_categorizer_download_clicked'
  | 'free_categorizer_upgrade_clicked'
  | 'free_categorizer_delete_clicked'
  | 'lead_submitted';

interface AnalyticsProperties {
  // Upload events
  ext?: string;
  isZip?: boolean;
  consentTraining?: boolean;
  errorCode?: string;
  
  // Parse events
  rows?: number;
  sourceType?: string;
  
  // Preview events
  watermark?: boolean;
  
  // Download events
  gate?: 'email' | 'bypass';
  
  // Lead events
  source?: string;
  
  // Common
  upload_id?: string;
  [key: string]: any;
}

class Analytics {
  private enabled: boolean;
  
  constructor() {
    this.enabled = typeof window !== 'undefined' && 
                   (process.env.NODE_ENV === 'production' || 
                    process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true');
  }
  
  /**
   * Track an event
   */
  track(event: AnalyticsEvent, properties: AnalyticsProperties = {}): void {
    if (!this.enabled || typeof window === 'undefined') {
      return;
    }
    
    // Try PostHog
    if (typeof (window as any).posthog !== 'undefined') {
      (window as any).posthog.capture(event, properties);
      return;
    }
    
    // Try GA4
    if (typeof (window as any).gtag !== 'undefined') {
      (window as any).gtag('event', event, properties);
      return;
    }
    
    // Try Amplitude
    if (typeof (window as any).amplitude !== 'undefined') {
      (window as any).amplitude.track(event, properties);
      return;
    }
    
    // Fallback: log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('[Analytics]', event, properties);
    }
  }
  
  /**
   * Identify user for tracking
   */
  identify(userId: string, traits: Record<string, any> = {}): void {
    if (!this.enabled || typeof window === 'undefined') {
      return;
    }
    
    if (typeof (window as any).posthog !== 'undefined') {
      (window as any).posthog.identify(userId, traits);
    }
    
    if (typeof (window as any).gtag !== 'undefined') {
      (window as any).gtag('set', 'user_properties', traits);
    }
    
    if (typeof (window as any).amplitude !== 'undefined') {
      (window as any).amplitude.setUserId(userId);
      (window as any).amplitude.setUserProperties(traits);
    }
  }
}

// Export singleton instance
export const analytics = new Analytics();

// Export helper functions
export function trackUploadStarted(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_upload_started', properties);
}

export function trackUploadFailed(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_upload_failed', properties);
}

export function trackParseOk(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_parse_ok', properties);
}

export function trackPreviewViewed(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_preview_viewed', properties);
}

export function trackVerifyClicked(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_verify_clicked', properties);
}

export function trackDownloadClicked(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_download_clicked', properties);
}

export function trackUpgradeClicked(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_upgrade_clicked', properties);
}

export function trackDeleteClicked(properties: AnalyticsProperties) {
  analytics.track('free_categorizer_delete_clicked', properties);
}

export function trackLeadSubmitted(properties: AnalyticsProperties) {
  analytics.track('lead_submitted', properties);
}

// Legacy/placeholder exports for other pages (to be implemented)
export function trackBridgeViewed() {
  // Placeholder - implement when GPT bridge analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackBridgeViewed');
  }
}

export function trackOpenGptClicked() {
  // Placeholder - implement when GPT bridge analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackOpenGptClicked');
  }
}

export function trackCheckoutClicked(planId: string, term: string) {
  // Placeholder - implement when pricing analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackCheckoutClicked', { planId, term });
  }
}

export function trackPurchase(amount: number, currency: string, plan: string) {
  // Placeholder - implement when purchase analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackPurchase', { amount, currency, plan });
  }
}

export function trackSubscriptionStarted(amount: number, currency: string, plan: string) {
  // Placeholder - implement when subscription analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackSubscriptionStarted', { amount, currency, plan });
  }
}

export function trackToolOpened(toolName: string) {
  // Placeholder - implement when tool analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackToolOpened', { toolName });
  }
}

export function trackRowsPreviewed(rowCount: number) {
  // Placeholder - implement when preview analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackRowsPreviewed', { rowCount });
  }
}

export function trackExportPaywalled(action: string) {
  // Placeholder - implement when paywall analytics is needed
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics] trackExportPaywalled', { action });
  }
}
