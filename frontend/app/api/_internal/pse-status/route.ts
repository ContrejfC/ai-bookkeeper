/**
 * Internal PSE Status Endpoint
 * =============================
 * Token-gated status check for PSE implementation.
 */

import { NextRequest, NextResponse } from 'next/server';
import { allBanks, getActiveBanks, toRouteSlug } from '@/lib/pse-banks';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const token = searchParams.get('token');
  const expectedToken = process.env.INTERNAL_STATUS_TOKEN;

  // Token gate
  if (!expectedToken || token !== expectedToken) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // Compute stats
  const activeBanks = getActiveBanks();
  const total = allBanks.length;
  const active = activeBanks.length;
  const noindex = total - active;
  const sampleRoutes = activeBanks.slice(0, 5).map(b => toRouteSlug(b.slug));

  return NextResponse.json({
    total,
    active,
    noindex,
    sampleRoutes,
    timestamp: new Date().toISOString(),
  });
}

