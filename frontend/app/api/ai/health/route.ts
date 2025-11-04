/**
 * AI Model Health Check
 * =====================
 * 
 * Tests AI model availability and configuration.
 * Returns which model is being used (primary or fallback).
 */

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

import { NextRequest, NextResponse } from "next/server";
import { respond, getModelConfig } from "@/lib/ai";

export async function GET(_req: NextRequest) {
  try {
    const config = getModelConfig();
    
    // Simple test to verify model works
    const r = await respond("Return only the string OK.", { temperature: 0 });
    
    return NextResponse.json({ 
      ok: true, 
      model: r.model, 
      fallback: Boolean(r.fallback), 
      sample: r.content.trim().slice(0, 64),
      config: {
        primary: config.primary,
        fallback: config.fallback,
        apiKeyConfigured: config.apiKeyConfigured
      }
    });
    
  } catch (e: any) {
    return NextResponse.json(
      { 
        ok: false, 
        error: String(e?.message || e),
        config: getModelConfig()
      }, 
      { status: 500 }
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

