/**
 * Server-Side Configuration Loader
 * 
 * This file can only be used in server-side contexts (API routes, server actions).
 * Do NOT import this in client components!
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { DEFAULT_FREE_TOOL_CONFIG } from './validators';

let cachedConfig: any = null;

/**
 * Load free tool configuration from YAML file (server-side only)
 */
export function loadFreeToolConfig() {
  if (cachedConfig) return cachedConfig;
  
  const configPath = process.env.FREE_TOOL_CONFIG_PATH || '../configs/free_tool.yaml';
  const fullPath = path.join(process.cwd(), configPath);
  
  try {
    const configContent = fs.readFileSync(fullPath, 'utf8');
    cachedConfig = yaml.load(configContent) as any;
    console.log('[CONFIG] Loaded free tool config from:', fullPath);
    return cachedConfig;
  } catch (error) {
    console.warn('[CONFIG] Failed to load YAML config, using defaults:', error);
    // Return defaults if config file doesn't exist
    cachedConfig = DEFAULT_FREE_TOOL_CONFIG;
    return cachedConfig;
  }
}

/**
 * Get a specific config value with fallback to default
 */
export function getConfigValue<T>(key: string, defaultValue: T): T {
  const config = loadFreeToolConfig();
  return config[key] !== undefined ? config[key] : defaultValue;
}



