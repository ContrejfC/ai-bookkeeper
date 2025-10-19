/**
 * Google Analytics 4 tracking utilities
 * 
 * Events tracked:
 * - bridge_viewed: GPT bridge page loaded
 * - open_gpt_clicked: User clicked to open ChatGPT
 * - tool_opened: CSV cleaner tool loaded
 * - rows_previewed: CSV preview rendered
 * - export_paywalled: User tried to export but hit paywall
 * - checkout_clicked: User clicked to start checkout
 * - purchase: Checkout completed (value = first month fee)
 * - subscription_started: Subscription created (value = first month fee)
 * - overage_charged: Monthly overage billed (value = overage amount)
 */

declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
  }
}

export interface GAEvent {
  event_name: string;
  event_params?: Record<string, any>;
}

/**
 * Send event to Google Analytics 4
 */
export function trackEvent(eventName: string, params?: Record<string, any>): void {
  if (typeof window === 'undefined') return;
  
  if (window.gtag) {
    window.gtag('event', eventName, params);
    console.log('[GA4]', eventName, params);
  } else {
    console.warn('[GA4] gtag not loaded, event not sent:', eventName);
  }
}

/**
 * Track page view
 */
export function trackPageView(url: string): void {
  trackEvent('page_view', {
    page_location: url,
    page_title: document.title
  });
}

/**
 * Track bridge viewed
 */
export function trackBridgeViewed(): void {
  trackEvent('bridge_viewed');
}

/**
 * Track open GPT clicked
 */
export function trackOpenGptClicked(): void {
  trackEvent('open_gpt_clicked');
}

/**
 * Track tool opened
 */
export function trackToolOpened(tool: string): void {
  trackEvent('tool_opened', { tool });
}

/**
 * Track rows previewed
 */
export function trackRowsPreviewed(rowCount: number): void {
  trackEvent('rows_previewed', { row_count: rowCount });
}

/**
 * Track export paywalled
 */
export function trackExportPaywalled(action: string): void {
  trackEvent('export_paywalled', { action });
}

/**
 * Track checkout clicked
 */
export function trackCheckoutClicked(plan: string, term: string): void {
  trackEvent('checkout_clicked', { plan, term });
}

/**
 * Track purchase
 */
export function trackPurchase(value: number, currency: string = 'USD', plan: string): void {
  trackEvent('purchase', {
    value,
    currency,
    plan,
    transaction_id: Date.now().toString()
  });
}

/**
 * Track subscription started
 */
export function trackSubscriptionStarted(value: number, currency: string = 'USD', plan: string): void {
  trackEvent('subscription_started', {
    value,
    currency,
    plan
  });
}

/**
 * Track overage charged
 */
export function trackOverageCharged(value: number, currency: string = 'USD'): void {
  trackEvent('overage_charged', {
    value,
    currency
  });
}

