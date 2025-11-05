/**
 * AI Model Wrapper - GPT-5 with Fallback
 * ======================================
 * 
 * Centralized OpenAI client with:
 * - GPT-5 as primary model
 * - GPT-4o fallback for rate limits/permissions
 * - Analytics tracking
 * - Error handling
 */

import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";
import { trackLLMModelUsed, trackLLMFallback } from "./analytics";

const PRIMARY = process.env.OPENAI_MODEL || "gpt-5-chat-latest";
const FALLBACK = process.env.OPENAI_FALLBACK_MODEL || "gpt-4o";

// Budget controls
const MAX_CALLS_PER_MIN = parseInt(process.env.AI_MAX_CALLS_PER_MIN || '60', 10);
const MAX_DAILY_USD = parseFloat(process.env.AI_MAX_DAILY_USD || '50');
const CIRCUIT_OPEN_SEC = parseInt(process.env.AI_CIRCUIT_OPEN_SEC || '300', 10);

// Circuit breaker state
let circuitOpenUntil = 0;
let callsThisMinute = 0;
let lastMinuteReset = Date.now();
let dailySpendUSD = 0;
let lastDayReset = new Date().toDateString();

// Lazy initialize client to avoid build-time errors
let _client: OpenAI | null = null;

function getClient(): OpenAI {
  if (!_client) {
    _client = new OpenAI({ 
      apiKey: process.env.OPENAI_API_KEY || 'sk-dummy-key-for-build'
    });
  }
  return _client;
}

export const client = getClient();

export interface AIResponse {
  ok: boolean;
  model: string;
  content: string;
  fallback?: boolean;
}

/**
 * Check budget limits and update counters
 * Throws if budget exceeded to trigger fallback
 */
function checkBudgetLimits() {
  const now = Date.now();
  const today = new Date().toDateString();
  
  // Reset minute counter
  if (now - lastMinuteReset > 60000) {
    callsThisMinute = 0;
    lastMinuteReset = now;
  }
  
  // Reset daily counter
  if (today !== lastDayReset) {
    dailySpendUSD = 0;
    lastDayReset = today;
  }
  
  // Increment call counter
  callsThisMinute++;
  
  // Check limits
  if (callsThisMinute > MAX_CALLS_PER_MIN) {
    // Open circuit breaker
    circuitOpenUntil = now + (CIRCUIT_OPEN_SEC * 1000);
    throw new Error(`AI_MAX_CALLS_PER_MIN exceeded (${MAX_CALLS_PER_MIN})`);
  }
  
  if (dailySpendUSD > MAX_DAILY_USD) {
    // Open circuit breaker
    circuitOpenUntil = now + (CIRCUIT_OPEN_SEC * 1000);
    throw new Error(`AI_MAX_DAILY_USD exceeded ($${MAX_DAILY_USD})`);
  }
}

/**
 * Call OpenAI with automatic fallback
 * 
 * @param input - The prompt/input text
 * @param options - Additional OpenAI API options
 * @returns Response with model used and content
 */
export async function respond(
  input: string, 
  options: Record<string, any> = {}
): Promise<AIResponse> {
  const t0 = Date.now();
  
  try {
    // Check circuit breaker
    if (Date.now() < circuitOpenUntil) {
      return {
        ok: true,
        model: 'degraded-heuristic',
        content: 'Service temporarily degraded. Please try again shortly.',
        fallback: true,
        // @ts-ignore
        llm_degraded: true
      };
    }
    
    // Check budget limits
    checkBudgetLimits();
    
    const c = getClient();
    
    // Try primary model (GPT-5) using chat completions
    const r = await c.chat.completions.create({
      model: PRIMARY,
      messages: [{ role: 'user' as const, content: input }],
      ...options,
    });
    
    // Track cost (rough estimate: $0.01 per 1K tokens)
    const estimatedCost = ((r.usage?.total_tokens || 0) / 1000) * 0.01;
    dailySpendUSD += estimatedCost;
    
    // Track successful primary model usage
    const latency_ms = Date.now() - t0;
    trackLLMModelUsed(r.model, false, { latency_ms, llm_degraded: false });
    
    return { 
      ok: true, 
      model: r.model, 
      content: r.choices[0]?.message?.content || ""
    };
    
  } catch (e: any) {
    // Check if we should fallback
    const shouldFallback =
      e?.status === 429 || 
      e?.status === 403 || 
      e?.status === 404 ||
      /insufficient|not enabled|quota|rate|permission/i.test(String(e?.message));
    
    if (!shouldFallback) {
      throw e;
    }
    
    // Log fallback for observability
    console.warn(`[AI] Falling back to ${FALLBACK} from ${PRIMARY}:`, e?.status, e?.message);
    
    // Track fallback
    trackLLMFallback(PRIMARY, FALLBACK, e?.message || 'unknown', { status: e?.status });
    
    const c = getClient();
    
    // Fallback to GPT-4o
    const r = await c.chat.completions.create({
      model: FALLBACK,
      messages: [{ role: 'user' as const, content: input }],
      ...options,
    });
    
    // Track fallback model usage
    trackLLMModelUsed(r.model, true);
    
    return { 
      ok: true, 
      model: r.model, 
      content: r.choices[0]?.message?.content || "",
      fallback: true
    };
  }
}

/**
 * Legacy completion function for chat-style APIs
 * Uses chat completions instead of responses
 */
export async function completion(
  messages: ChatCompletionMessageParam[],
  options: Record<string, any> = {}
): Promise<AIResponse> {
  try {
    const c = getClient();
    
    // Try primary model
    const r = await c.chat.completions.create({
      model: PRIMARY,
      messages,
      ...options,
    });
    
    // Track successful primary model usage
    trackLLMModelUsed(r.model, false);
    
    return {
      ok: true,
      model: r.model,
      content: r.choices[0]?.message?.content || ""
    };
    
  } catch (e: any) {
    // Check if we should fallback
    const shouldFallback =
      e?.status === 429 || 
      e?.status === 403 || 
      e?.status === 404 ||
      /insufficient|not enabled|quota|rate|permission/i.test(String(e?.message));
    
    if (!shouldFallback) {
      throw e;
    }
    
    console.warn(`[AI] Falling back to ${FALLBACK} from ${PRIMARY}:`, e?.status, e?.message);
    
    // Track fallback
    trackLLMFallback(PRIMARY, FALLBACK, e?.message || 'unknown', { status: e?.status });
    
    const c = getClient();
    
    // Fallback to GPT-4o
    const r = await c.chat.completions.create({
      model: FALLBACK,
      messages,
      ...options,
    });
    
    // Track fallback model usage
    trackLLMModelUsed(r.model, true);
    
    return {
      ok: true,
      model: r.model,
      content: r.choices[0]?.message?.content || "",
      fallback: true
    };
  }
}

/**
 * Get current model configuration
 */
export function getModelConfig() {
  return {
    primary: PRIMARY,
    fallback: FALLBACK,
    apiKeyConfigured: !!process.env.OPENAI_API_KEY
  };
}

