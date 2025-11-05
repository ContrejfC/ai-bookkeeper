#!/usr/bin/env tsx
/**
 * Write Build Info
 * ================
 * 
 * Captures git metadata at build time and writes to .next/meta/BUILD_INFO.json
 * This provides a fallback when VERCEL_GIT_* env vars are not available.
 * 
 * Runs as prebuild step in package.json
 */

import { execSync } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

/**
 * Execute shell command and return output
 */
function sh(cmd: string): string {
  try {
    return execSync(cmd, { 
      stdio: ['ignore', 'pipe', 'ignore'],
      encoding: 'utf-8'
    }).trim();
  } catch {
    return '';
  }
}

function main() {
  console.log('📝 Writing build info...');
  
  const data = {
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA || sh('git rev-parse --short HEAD'),
    commitRef: process.env.VERCEL_GIT_COMMIT_REF || sh('git rev-parse --abbrev-ref HEAD'),
    commitMessage: process.env.VERCEL_GIT_COMMIT_MESSAGE || sh('git log -1 --pretty=%s'),
    repoOwner: process.env.VERCEL_GIT_REPO_OWNER || '',
    repoSlug: process.env.VERCEL_GIT_REPO_SLUG || 'ai-bookkeeper',
    timeIso: new Date().toISOString(),
  };
  
  // Create meta directory
  const metaDir = join(process.cwd(), '.next', 'meta');
  mkdirSync(metaDir, { recursive: true });
  
  // Write build info
  const filePath = join(metaDir, 'BUILD_INFO.json');
  writeFileSync(filePath, JSON.stringify(data, null, 2));
  
  console.log(`✅ Wrote build info to ${filePath}`);
  console.log(`   Commit: ${data.commitSha} (${data.commitRef})`);
  console.log(`   Message: ${data.commitMessage.slice(0, 60)}...`);
}

main();

