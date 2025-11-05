/**
 * Feature Flags
 * ==============
 * Centralized feature flag configuration for runtime and build-time checks.
 */

export interface FeatureFlags {
  // Free tier limits
  freeMaxRows: number;
  freeMaxFileMb: number;
  freeRetentionHours: number;
  
  // Feature toggles
  enableLLMCategorization: boolean;
  enableOFXQFXUpload: boolean;
  enableEmailGate: boolean;
  
  // LLM configuration
  llmEnabled: boolean;
  llmModel: string;
  llmFallbackModel: string;
  
  // Site configuration
  siteUrl: string;
  soc2Status: string;
}

/**
 * Get feature flags from environment
 * Safe to call client or server-side
 */
export function getFlags(): FeatureFlags {
  const isServer = typeof window === 'undefined';
  
  // Server-side: read from process.env
  if (isServer) {
    const hasOpenAIKey = !!process.env.OPENAI_API_KEY;
    
    return {
      freeMaxRows: parseInt(process.env.FREE_MAX_ROWS || '500', 10),
      freeMaxFileMb: parseInt(process.env.FREE_MAX_FILE_MB || '10', 10),
      freeRetentionHours: parseInt(process.env.FREE_RETENTION_HOURS || '24', 10),
      
      enableLLMCategorization: 
        process.env.ENABLE_LLM_CATEGORIZATION === 'true' || hasOpenAIKey,
      enableOFXQFXUpload: process.env.ENABLE_OFX_QFX_UPLOAD === 'true',
      enableEmailGate: process.env.NEXT_PUBLIC_ENABLE_EMAIL_GATE === 'true',
      
      llmEnabled: hasOpenAIKey,
      llmModel: process.env.OPENAI_MODEL || 'gpt-5-chat-latest',
      llmFallbackModel: process.env.OPENAI_FALLBACK_MODEL || 'gpt-4o',
      
      siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app',
      soc2Status: process.env.SOC2_STATUS || 'aligned',
    };
  }
  
  // Client-side: read from NEXT_PUBLIC_ vars only
  return {
    freeMaxRows: parseInt(process.env.NEXT_PUBLIC_FREE_MAX_ROWS || '500', 10),
    freeMaxFileMb: parseInt(process.env.NEXT_PUBLIC_FREE_MAX_FILE_MB || '10', 10),
    freeRetentionHours: 24,
    
    enableLLMCategorization: false, // Client doesn't know about API key
    enableOFXQFXUpload: process.env.NEXT_PUBLIC_ENABLE_OFX_QFX === 'true',
    enableEmailGate: process.env.NEXT_PUBLIC_ENABLE_EMAIL_GATE === 'true',
    
    llmEnabled: false,
    llmModel: '',
    llmFallbackModel: '',
    
    siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'https://ai-bookkeeper.app',
    soc2Status: 'aligned',
  };
}

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  const flags = getFlags();
  return Boolean(flags[feature]);
}

