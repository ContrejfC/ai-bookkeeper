/**
 * Categorization Pipeline
 * ========================
 * Orchestrates Rules → Embeddings → LLM with confidence gating
 */

import type { Transaction } from '../parse/schema';
import { applyRules, type Rule } from './rules';
import { matchByEmbedding } from './embeddings';
import { categorizeWithLLM } from './llm';
import { getFlags } from '../flags';

const CONFIDENCE_THRESHOLD = 0.7;

/**
 * Categorize all transactions through the pipeline
 */
export async function categorizeTransactions(
  transactions: Transaction[],
  customRules: Rule[] = []
): Promise<Transaction[]> {
  const flags = getFlags();
  const llmEnabled = flags.enableLLMCategorization;
  
  const categorized = [...transactions];
  const needsLLM: Transaction[] = [];
  
  // Stage 1 & 2: Rules and Embeddings (synchronous)
  for (const txn of categorized) {
    // Try rules first
    const ruleResult = applyRules(txn, customRules);
    if (ruleResult) {
      txn.category = ruleResult.category;
      txn.confidence = ruleResult.explanation.confidence;
      txn.source = 'rule';
      txn.explanation = ruleResult.explanation;
      txn.needsReview = false;
      continue;
    }
    
    // Try embeddings
    const embeddingResult = matchByEmbedding(txn);
    if (embeddingResult) {
      txn.category = embeddingResult.category;
      txn.confidence = embeddingResult.explanation.confidence;
      txn.source = 'embedding';
      txn.explanation = embeddingResult.explanation;
      txn.needsReview = txn.confidence < CONFIDENCE_THRESHOLD;
      continue;
    }
    
    // No match yet - needs LLM or defaults to uncategorized
    if (llmEnabled) {
      needsLLM.push(txn);
    } else {
      txn.category = 'Uncategorized';
      txn.confidence = 0.5;
      txn.source = 'manual';
      txn.needsReview = true;
    }
  }
  
  // Stage 3: LLM (async, batched)
  if (llmEnabled && needsLLM.length > 0) {
    try {
      const llmResults = await categorizeWithLLM(needsLLM);
      
      for (const txn of needsLLM) {
        const result = llmResults.get(txn.id);
        if (result) {
          txn.category = result.category;
          txn.confidence = result.explanation.confidence;
          txn.source = 'llm';
          txn.explanation = result.explanation;
          txn.needsReview = txn.confidence < CONFIDENCE_THRESHOLD;
        } else {
          // LLM didn't return a result for this transaction
          txn.category = 'Uncategorized';
          txn.confidence = 0.5;
          txn.source = 'manual';
          txn.needsReview = true;
        }
      }
    } catch (error) {
      console.error('[Pipeline] LLM categorization failed:', error);
      // Fall back to uncategorized
      for (const txn of needsLLM) {
        txn.category = 'Uncategorized';
        txn.confidence = 0.5;
        txn.source = 'manual';
        txn.needsReview = true;
      }
    }
  }
  
  return categorized;
}

/**
 * Re-categorize transactions with updated rules
 */
export async function recategorize(
  transactions: Transaction[],
  customRules: Rule[]
): Promise<Transaction[]> {
  // Reset categories for recategorization
  const reset = transactions.map(t => ({
    ...t,
    category: undefined,
    confidence: undefined,
    source: undefined,
    explanation: undefined,
    needsReview: undefined,
  }));
  
  return categorizeTransactions(reset, customRules);
}

