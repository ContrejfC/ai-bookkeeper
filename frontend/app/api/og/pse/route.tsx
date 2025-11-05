/**
 * PSE OG Image Generator
 * =======================
 * 
 * Dynamic Open Graph image generation for bank export guides.
 * Text-only, neutral colors, no logos, trademark-safe.
 */

import { ImageResponse } from 'next/og';
import { NextRequest } from 'next/server';
import { getBankBySlug } from '@/lib/pse-banks';

export const runtime = 'edge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const slug = searchParams.get('slug');

    if (!slug) {
      return new Response('Missing slug parameter', { status: 400 });
    }

    const bank = getBankBySlug(slug);

    if (!bank) {
      return new Response('Bank not found', { status: 404 });
    }

    // Generate OG image with text only (no logos, neutral colors)
    return new ImageResponse(
      (
        <div
          style={{
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f9fafb',
            padding: '60px 80px',
          }}
        >
          {/* Subtle background pattern */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundImage:
                'radial-gradient(circle at 25px 25px, #e5e7eb 2%, transparent 0%), radial-gradient(circle at 75px 75px, #e5e7eb 2%, transparent 0%)',
              backgroundSize: '100px 100px',
              opacity: 0.4,
            }}
          />

          {/* Content */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              zIndex: 1,
            }}
          >
            {/* Title */}
            <div
              style={{
                fontSize: 64,
                fontWeight: 700,
                color: '#111827',
                marginBottom: 20,
                maxWidth: '900px',
                lineHeight: 1.2,
              }}
            >
              {bank.bankName}
            </div>

            {/* Subtitle */}
            <div
              style={{
                fontSize: 36,
                color: '#6b7280',
                marginBottom: 40,
                fontWeight: 500,
              }}
            >
              Export Transactions to CSV
            </div>

            {/* Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: '#10b981',
                color: 'white',
                padding: '12px 32px',
                borderRadius: 8,
                fontSize: 24,
                fontWeight: 600,
              }}
            >
              Free Step-by-Step Guide
            </div>

            {/* Footer */}
            <div
              style={{
                marginTop: 60,
                fontSize: 20,
                color: '#9ca3af',
                fontWeight: 500,
              }}
            >
              ai-bookkeeper.app/guides
            </div>
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
        headers: {
          'cache-control': 'public, max-age=86400, stale-while-revalidate=604800',
        },
      }
    );
  } catch (e: any) {
    console.error('PSE OG image generation failed:', e);
    return new Response('Failed to generate OG image', { status: 500 });
  }
}

