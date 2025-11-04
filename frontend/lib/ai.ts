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
  try {
    const c = getClient();
    
    // Try primary model (GPT-5) using chat completions
    const r = await c.chat.completions.create({
      model: PRIMARY,
      messages: [{ role: 'user' as const, content: input }],
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

