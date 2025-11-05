/**
 * Build Provenance Endpoint
 * =========================
 * 
 * Exposes build and environment metadata for verification.
 * Anyone can verify which commit, branch, and environment they're viewing.
 */

import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

/**
 * Get build git metadata from Vercel environment
 */
function getBuildGit() {
  return {
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA || '',
    commitRef: process.env.VERCEL_GIT_COMMIT_REF || '',
    commitMessage: process.env.VERCEL_GIT_COMMIT_MESSAGE || '',
    repoOwner: process.env.VERCEL_GIT_REPO_OWNER || '',
    repoSlug: process.env.VERCEL_GIT_REPO_SLUG || '',
  };
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

  return new Response(JSON.stringify(data, null, 2), {
    status: 200,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

