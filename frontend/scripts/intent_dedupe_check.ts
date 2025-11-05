#!/usr/bin/env ts-node
/**
 * Intent Deduplication Guard
 * ==========================
 * 
 * Scans data/pse.json and fails CI if multiple slugs share the same primaryIntent.
 * Prevents keyword cannibalization and duplicate content issues.
 * 
 * Usage:
 *   npx ts-node scripts/intent_dedupe_check.ts
 *   Exit 0: No duplicates found
 *   Exit 1: Duplicates detected
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface PSEPage {
  slug: string;
  primaryIntent?: string;
  status?: 'active' | 'noindex';
  title?: string;
}

function main() {
  const pseFilePath = join(__dirname, '../data/pse.json');
  
  // Check if file exists
  if (!existsSync(pse FilePath)) {
    console.log('✅ No pse.json file found - skipping intent deduplication check');
    process.exit(0);
  }
  
  // Read and parse
  let data: PSEPage[];
  try {
    const fileContent = readFileSync(pseFilePath, 'utf-8');
    data = JSON.parse(fileContent);
  } catch (error) {
    console.error('❌ Failed to read or parse data/pse.json:', error);
    process.exit(1);
  }
  
  // Track intents
  const intentMap = new Map<string, string[]>();
  
  for (const page of data) {
    if (page.primaryIntent) {
      const intent = page.primaryIntent.toLowerCase().trim();
      
      if (!intentMap.has(intent)) {
        intentMap.set(intent, []);
      }
      
      intentMap.get(intent)!.push(page.slug);
    }
  }
  
  // Find duplicates
  const duplicates: Array<{ intent: string; slugs: string[] }> = [];
  
  for (const [intent, slugs] of intentMap.entries()) {
    if (slugs.length > 1) {
      duplicates.push({ intent, slugs });
    }
  }
  
  // Report results
  if (duplicates.length === 0) {
    console.log(`✅ Intent deduplication check passed`);
    console.log(`   Checked ${data.length} pages, ${intentMap.size} unique intents`);
    process.exit(0);
  } else {
    console.error(`❌ Intent deduplication check FAILED`);
    console.error(`   Found ${duplicates.length} duplicate intent(s):\n`);
    
    for (const dup of duplicates) {
      console.error(`   Intent: "${dup.intent}"`);
      console.error(`   Slugs: ${dup.slugs.join(', ')}`);
      console.error('');
    }
    
    console.error('   Fix: Ensure each slug has a unique primaryIntent value');
    console.error('   or remove the primaryIntent field from duplicate pages.\n');
    
    process.exit(1);
  }
}

main();

