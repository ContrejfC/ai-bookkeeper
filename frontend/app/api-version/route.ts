/**
 * Build Provenance Endpoint
 * =========================
 * 
 * Exposes build and environment metadata for verification.
 * Anyone can verify which commit, branch, and environment they're viewing.
 */

import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

/**
 * Get git metadata from Vercel environment variables
 */
function envGit() {
  return {
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA || '',
    commitRef: process.env.VERCEL_GIT_COMMIT_REF || '',
    commitMessage: process.env.VERCEL_GIT_COMMIT_MESSAGE || '',
    repoOwner: process.env.VERCEL_GIT_REPO_OWNER || '',
    repoSlug: process.env.VERCEL_GIT_REPO_SLUG || '',
  };
}

/**
 * Get git metadata from build-time file (fallback)
 */
function fileGit() {
  const buildInfoPath = join(process.cwd(), '.next', 'meta', 'BUILD_INFO.json');
  
  if (!existsSync(buildInfoPath)) {
    return null;
  }
  
  try {
    const content = readFileSync(buildInfoPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error('[api-version] Failed to read BUILD_INFO.json:', error);
    return null;
  }
}

/**
 * Get build git metadata with fallback
 */
function getBuildGit() {
  const eg = envGit();
  
  // Check if env vars are populated
  const missing = !eg.commitSha || !eg.commitRef || !eg.commitMessage;
  
  if (missing) {
    // Try file fallback
    const fg = fileGit();
    if (fg) {
      console.log('[api-version] Using file git fallback');
      return fg;
    }
  }
  
  return eg;
}

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const host = req.headers.get('host') ?? url.host;
  const git = getBuildGit();

  const data = {
    name: 'ai-bookkeeper',
    host,
    protocol: url.protocol.replace(':', ''),
    env: process.env.VERCEL_ENV || process.env.NODE_ENV || 'unknown',
    vercel: {
      env: process.env.VERCEL_ENV || null,
      url: process.env.VERCEL_URL || null,
      projectProdUrl: process.env.VERCEL_PROJECT_PRODUCTION_URL || null,
    },
    git: {
      commitSha: git.commitSha,
      commitRef: git.commitRef,
      commitMessage: git.commitMessage,
      repoOwner: git.repoOwner,
      repoSlug: git.repoSlug,
    },
    build: {
      timeIso: new Date().toISOString(),
      soc2Status: process.env.SOC2_STATUS ?? 'aligned',
      freeMaxRows: Number(process.env.FREE_MAX_ROWS ?? 500),
    },
    pages: [
      '/free/categorizer',
      '/privacy',
      '/terms',
      '/security'
    ],
    apis: [
      '/api/free/categorizer/upload',
      '/api/free/categorizer/lead',
      '/api/free/categorizer/uploads/{id}'
    ],
  };

  return NextResponse.json(data, {
    status: 200,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

