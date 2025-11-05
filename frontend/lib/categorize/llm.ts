/**
 * LLM-Based Categorization
 * ==========================
 * GPT-5 categorization with batching and cost controls
 */

import type { Transaction, Explanation } from '../parse/schema';
import { respond } from '../ai';
import { QBO_CATEGORIES } from '../categories';

const BATCH_SIZE = 50;

/**
 * Categorize transactions using LLM (batched)
 */
export async function categor

izeWithLLM(
  transactions: Transaction[]
): Promise<Map<string, { category: string; explanation: Explanation }>> {
  const results = new Map();
  
  // Process in batches
  for (let i = 0; i < transactions.length; i += BATCH_SIZE) {
    const batch = transactions.slice(i, i + BATCH_SIZE);
    const batchResults = await categorizeBatch(batch);
    
    for (const [id, result] of batchResults.entries()) {
      results.set(id, result);
    }
  }
  
  return results;
}

/**
 * Categorize a batch of transactions
 */
async function categorizeBatch(
  batch: Transaction[]
): Promise<Map<string, { category: string; explanation: Explanation }>> {
  const t0 = Date.now();
  
  const categoryNames = QBO_CATEGORIES.map(c => c.name);
  
  const prompt = `Categorize these bank transactions. Return ONLY a JSON array with objects: {"id":"<txn-id>","category":"<category-name>","confidence":0.0-1.0}.

Categories: ${categoryNames.join(', ')}

Transactions:
${batch.map((t, i) => `${i + 1}. ID:${t.id} Date:${t.date.toISOString().split('T')[0]} Amount:${t.amount} Desc:"${t.description}"`).join('\n')}

Return valid JSON only, no markdown:`;

  try {
    const response = await respond(prompt, { temperature: 0.3 });
    
    if (!response.ok) {
      throw new Error('LLM request failed');
    }
    
    // Parse JSON response
    const jsonMatch = response.content.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      throw new Error('Invalid LLM response format');
    }
    
    const results = JSON.parse(jsonMatch[0]);
    const map = new Map();
    
    for (const result of results) {
      if (result.id && result.category) {
        map.set(result.id, {
          category: result.category,
          explanation: {
            stage: 'llm',
            confidence: result.confidence || 0.8,
            llmModel: response.model,
            llmHint: 'LLM categorization',
            pipelineTimeMs: Date.now() - t0,
          },
        });
      }
    }
    
    return map;
  } catch (error) {
    console.error('[LLM Categorization] Error:', error);
    // Return empty map - will use fallback categories
    return new Map();
  }
}

