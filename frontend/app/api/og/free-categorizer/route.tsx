/**
 * Dynamic OG Image for Free Categorizer
 * =====================================
 */

import { ImageResponse } from 'next/og';
import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  try {
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
            background

: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          {/* Main Content */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '60px',
            }}
          >
            {/* Icon */}
            <div
              style={{
                fontSize: 120,
                marginBottom: 30,
              }}
            >
              📊
            </div>
            
            {/* Title */}
            <div
              style={{
                fontSize: 72,
                fontWeight: 'bold',
                background: 'linear-gradient(90deg, #10b981 0%, #06b6d4 100%)',
                backgroundClip: 'text',
                color: 'transparent',
                textAlign: 'center',
                marginBottom: 20,
              }}
            >
              Free Bank Transaction Categorizer
            </div>
            
            {/* Subtitle */}
            <div
              style={{
                fontSize: 32,
                color: '#94a3b8',
                textAlign: 'center',
                marginBottom: 40,
              }}
            >
              Upload. Auto-categorize. Download CSV or export to QuickBooks.
            </div>
            
            {/* Features */}
            <div
              style={{
                display: 'flex',
                gap: 30,
                fontSize: 28,
                color: '#10b981',
              }}
            >
              <span>CSV</span>
              <span style={{ color: '#475569' }}>•</span>
              <span>OFX</span>
              <span style={{ color: '#475569' }}>•</span>
              <span>QFX</span>
              <span style={{ color: '#475569' }}>•</span>
              <span>QuickBooks Export</span>
            </div>
          </div>
          
          {/* Footer */}
          <div
            style={{
              position: 'absolute',
              bottom: 40,
              left: 60,
              fontSize: 24,
              color: '#64748b',
            }}
          >
            AI Bookkeeper
          </div>
          
          {/* Trust Badge */}
          <div
            style={{
              position: 'absolute',
              bottom: 40,
              right: 60,
              fontSize: 20,
              color: '#64748b',
              display: 'flex',
              gap: 15,
            }}
          >
            <span>🔒 SOC 2-aligned</span>
            <span>•</span>
            <span>24hr deletion</span>
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
        headers: {
          'Cache-Control': 'public, max-age=86400', // 24 hours
        },
      }
    );
  } catch (error) {
    console.error('OG image generation error:', error);
    return new Response('Failed to generate image', { status: 500 });
  }
}

