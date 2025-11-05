#!/usr/bin/env tsx
/**
 * PSE Asset Safety Checker
 * =========================
 * 
 * Ensures PSE guide pages don't use bank logos or brand colors.
 * Prevents trademark violations in programmatic SEO content.
 * 
 * Usage: tsx scripts/check_pse_assets.ts
 * Exit code: 0 if safe, 1 if violations found
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, extname } from 'path';

// Banned brand color hex codes (common bank brand colors)
const BANNED_COLORS = [
  '#003087', // Chase blue
  '#0062ff', // Bank of America blue
  '#d71e28', // Wells Fargo red
  '#003d79', // Citi blue
  '#004976', // Capital One blue
  '#00205b', // US Bank blue
  '#ff0000', // Generic brand red
  '#005eb8', // PNC blue
  '#330072', // Truist purple
  '#007837', // TD green
  '#009639', // Regions green
  '#e31837', // Fifth Third red
  '#004b8d', // KeyBank blue
  '#046a38', // Huntington green
  '#ec0000', // Santander red
  '#0047bb', // American Express blue
  '#003087', // PayPal blue (duplicate but kept for clarity)
  '#6772e5', // Stripe purple
];

// Normalize hex colors for comparison
function normalizeHex(hex: string): string {
  return hex.toLowerCase().replace(/[^0-9a-f]/g, '');
}

// Check if content contains banned logos or brand colors
function checkFileContent(filePath: string, content: string): string[] {
  const violations: string[] = [];
  
  // Check for logo imports
  const logoImportRegex = /import\s+.*from\s+['"].*\/logos\/.*['"]/gi;
  const logoMatches = content.match(logoImportRegex);
  if (logoMatches) {
    violations.push(`${filePath}: Contains logo import: ${logoMatches.join(', ')}`);
  }
  
  // Check for public/logos path references
  const logoPathRegex = /['"]\/logos\/[^'"]+['"]/gi;
  const logoPathMatches = content.match(logoPathRegex);
  if (logoPathMatches) {
    violations.push(`${filePath}: References logo path: ${logoPathMatches.join(', ')}`);
  }
  
  // Check for banned brand colors
  const hexColorRegex = /#[0-9a-fA-F]{6}\b/g;
  const colorMatches = content.match(hexColorRegex);
  if (colorMatches) {
    const normalizedBanned = BANNED_COLORS.map(normalizeHex);
    for (const color of colorMatches) {
      const normalized = normalizeHex(color);
      if (normalizedBanned.includes(normalized)) {
        violations.push(`${filePath}: Uses banned brand color: ${color}`);
      }
    }
  }
  
  return violations;
}

// Recursively check files in directory
function checkDirectory(dirPath: string): string[] {
  const violations: string[] = [];
  
  try {
    const entries = readdirSync(dirPath);
    
    for (const entry of entries) {
      const fullPath = join(dirPath, entry);
      const stat = statSync(fullPath);
      
      if (stat.isDirectory()) {
        violations.push(...checkDirectory(fullPath));
      } else if (stat.isFile()) {
        const ext = extname(entry);
        if (['.tsx', '.ts', '.jsx', '.js'].includes(ext)) {
          const content = readFileSync(fullPath, 'utf-8');
          violations.push(...checkFileContent(fullPath, content));
        }
      }
    }
  } catch (error) {
    console.error(`Error checking directory ${dirPath}:`, error);
  }
  
  return violations;
}

async function main() {
  console.log('🔍 Checking PSE assets for trademark safety...\n');
  
  const violations: string[] = [];
  
  // Check PSE guide pages
  const guidesPath = join(process.cwd(), 'app', 'guides');
  console.log(`Checking: ${guidesPath}`);
  violations.push(...checkDirectory(guidesPath));
  
  // Check PSE components
  const componentsPath = join(process.cwd(), 'components');
  if (existsSync(componentsPath)) {
    const componentFiles = readdirSync(componentsPath).filter(f => f.startsWith('PSE') && (f.endsWith('.ts') || f.endsWith('.tsx')));
    for (const file of componentFiles) {
      const fullPath = join(componentsPath, file);
      console.log(`Checking: ${fullPath}`);
      const content = readFileSync(fullPath, 'utf-8');
      violations.push(...checkFileContent(fullPath, content));
    }
  }
  
  // Check PSE OG endpoint
  const ogPath = join(process.cwd(), 'app', 'api', 'og', 'pse');
  if (existsSync(ogPath) && statSync(ogPath).isDirectory()) {
    console.log(`Checking: ${ogPath}`);
    violations.push(...checkDirectory(ogPath));
  }
  
  // Check PSE data file
  const dataPath = join(process.cwd(), 'data', 'pse', 'banks.json');
  console.log(`Checking: ${dataPath}`);
  const dataContent = readFileSync(dataPath, 'utf-8');
  violations.push(...checkFileContent(dataPath, dataContent));
  
  console.log();
  
  // Report results
  if (violations.length > 0) {
    console.error('❌ Trademark safety violations found:\n');
    for (const violation of violations) {
      console.error(`  - ${violation}`);
    }
    console.error(`\n❌ Total violations: ${violations.length}`);
    console.error('\nFix these violations before deploying PSE pages.');
    console.error('Avoid using bank logos or brand colors in PSE content.');
    process.exit(1);
  } else {
    console.log('✅ No trademark safety violations found.');
    console.log('✅ PSE assets are trademark-safe.');
    process.exit(0);
  }
}

main().catch((error) => {
  console.error('Error running PSE asset check:', error);
  process.exit(1);
});

