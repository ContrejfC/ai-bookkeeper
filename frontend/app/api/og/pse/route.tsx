/**
 * PSE OG Image Generator
 * =======================
 * 
 * Dynamic Open Graph image generation for bank export guides.
 * Text-only, neutral colors, no logos, trademark-safe.
 */

import { ImageResponse } from 'next/og';
import { NextResponse } from 'next/server';
import { findBankByRouteSlug } from '@/lib/pse-banks';

export const runtime = 'edge'; // Faster cold-start for OG images

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const slug = searchParams.get('slug') || '';
  const bank = findBankByRouteSlug(slug);

  if (!bank) {
    return new NextResponse('Invalid slug', { status: 400 });
  }

  // Generate OG image with text only (no logos, neutral colors)
  const img = new ImageResponse(
    (
      <div
        style={{
          width: 1200,
          height: 630,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          background: 'white',
          padding: 64,
          fontSize: 48,
          color: '#111827',
        }}
      >
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            marginBottom: 16,
            textAlign: 'center',
          }}
        >
          {bank.name}: Export to CSV
        </div>
        <div
          style={{
            fontSize: 32,
            color: '#374151',
            textAlign: 'center',
          }}
        >
          Step-by-step guide • ai-bookkeeper.app
        </div>
      </div>
    ),
    { width: 1200, height: 630 }
  );

  // Add cache headers for performance
  img.headers.set('Cache-Control', 'public, max-age=86400, stale-while-revalidate=604800');
  
  return img;
}
