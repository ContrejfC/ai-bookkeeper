/**
 * Embedding-Based Categorization
 * ================================
 * Simple cosine similarity matching against merchant lexicon
 */

import type { Transaction, Explanation } from '../parse/schema';

// Tiny merchant lexicon (keywords → category)
// In production, this could be expanded or use actual embeddings
const MERCHANT_LEXICON: Record<string, { category: string; keywords: string[] }> = {
  'coffee': { category: 'Meals & Entertainment', keywords: ['coffee', 'cafe', 'espresso', 'latte'] },
  'fuel': { category: 'Auto & Vehicle', keywords: ['gas', 'fuel', 'petrol', 'gasoline'] },
  'groceries': { category: 'Supplies', keywords: ['grocery', 'market', 'supermarket', 'food'] },
  'software': { category: 'Software & Subscriptions', keywords: ['saas', 'software', 'app', 'subscription'] },
  'hosting': { category: 'Software & Subscriptions', keywords: ['hosting', 'server', 'cloud', 'aws', 'vercel'] },
  'restaurant': { category: 'Meals & Entertainment', keywords: ['restaurant', 'dining', 'food', 'eatery'] },
  'office': { category: 'Office Supplies', keywords: ['office', 'supplies', 'stationery', 'paper'] },
  'travel': { category: 'Travel', keywords: ['airline', 'hotel', 'flight', 'airbnb'] },
  'utilities': { category: 'Utilities', keywords: ['electric', 'water', 'utility', 'internet', 'phone'] },
  'bank': { category: 'Bank Fees & Charges', keywords: ['bank fee', 'service charge', 'monthly fee'] },
};

const SIMILARITY_THRESHOLD = 0.78;

/**
 * Find category using embedding/lexicon matching
 */
export function matchByEmbedding(txn: Transaction): {
  category: string;
  explanation: Explanation;
} | null {
  const t0 = Date.now();
  const description = txn.description.toLowerCase();
  
  let bestMatch: { key: string; similarity: number } | null = null;
  
  for (const [key, data] of Object.entries(MERCHANT_LEXICON)) {
    const similarity = calculateSimilarity(description, data.keywords);
    
    if (similarity > SIMILARITY_THRESHOLD && (!bestMatch || similarity > bestMatch.similarity)) {
      bestMatch = { key, similarity };
    }
  }
  
  if (bestMatch) {
    const category = MERCHANT_LEXICON[bestMatch.key].category;
    return {
      category,
      explanation: {
        stage: 'embedding',
        confidence: bestMatch.similarity,
        topMatch: bestMatch.key,
        similarity: bestMatch.similarity,
        pipelineTimeMs: Date.now() - t0,
      },
    };
  }
  
  return null;
}

/**
 * Simple keyword matching (cosine similarity approximation)
 * Returns score 0.0-1.0
 */
function calculateSimilarity(text: string, keywords: string[]): number {
  const textWords = text.toLowerCase().split(/\s+/);
  const matches = keywords.filter(kw => textWords.some(w => w.includes(kw) || kw.includes(w)));
  
  // Score based on percentage of keywords matched
  return matches.length / Math.max(keywords.length, 1);
}
