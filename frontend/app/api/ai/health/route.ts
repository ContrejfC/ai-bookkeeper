/**
 * AI Model Health Check
 * =====================
 * 
 * Tests AI model availability and configuration.
 * ALWAYS returns 200 JSON (never throws or returns 500).
 * Returns which model is being used (primary or fallback).
 */

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from "next/server";
import { respond, getModelConfig } from "@/lib/ai";

export async function GET(_req: NextRequest) {
  const t0 = Date.now();
  const timestamp = new Date().toISOString();
  
  try {
    // Check if API key is configured
    if (!process.env.OPENAI_API_KEY) {
      return NextResponse.json(
        { 
          ok: false, 
          error: "missing_api_key", 
          timestamp,
          config: getModelConfig()
        },
        { 
          status: 200,
          headers: { "Cache-Control": "no-store" }
        }
      );
    }
    
    const config = getModelConfig();
    
    // Simple test to verify model works
    const r = await respond("Return only the string OK.", { temperature: 0 });
    const latency_ms = Date.now() - t0;
    
    return NextResponse.json(
      { 
        ok: true, 
        model: r.model, 
        fallback: Boolean(r.fallback),
        latency_ms,
        sample: r.content.trim().slice(0, 64),
        timestamp,
        config: {
          primary: config.primary,
          fallback: config.fallback,
          apiKeyConfigured: config.apiKeyConfigured
        }
      },
      { 
        status: 200,
        headers: { "Cache-Control": "no-store" }
      }
    );
    
  } catch (e: any) {
    const latency_ms = Date.now() - t0;
    
    // Always return 200, even on errors
    return NextResponse.json(
      { 
        ok: false, 
        error: String(e?.message || e),
        latency_ms,
        timestamp,
        config: getModelConfig()
      }, 
      { 
        status: 200,
        headers: { "Cache-Control": "no-store" }
      }
    );
  }
}

// Method guards
export async function POST() { 
  return new Response('Method Not Allowed', { 
    status: 405, 
    headers: { 'Allow': 'GET' } 
  }); 
}

export async function PUT() { 
  return new Response('Method Not Allowed', { 
    status: 405, 
    headers: { 'Allow': 'GET' } 
  }); 
}

export async function PATCH() { 
  return new Response('Method Not Allowed', { 
    status: 405, 
    headers: { 'Allow': 'GET' } 
  }); 
}

export async function DELETE() { 
  return new Response('Method Not Allowed', { 
    status: 405, 
    headers: { 'Allow': 'GET' } 
  }); 
}

