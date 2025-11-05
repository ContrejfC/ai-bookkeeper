/**
 * Categorization Web Worker
 * ===========================
 * Non-blocking CSV parsing and embedding-based categorization
 */

import { parseCSV } from '../lib/parse/csv';
import { parseOFX, isOFX } from '../lib/parse/ofx';
import { parseQFX, isQFX } from '../lib/parse/qfx';
import { applyRules } from '../lib/categorize/rules';
import { matchByEmbedding } from '../lib/categorize/embeddings';
import type { Transaction, ColumnMapping } from '../lib/parse/schema';

export interface WorkerMessage {
  type: 'parse' | 'categorize';
  payload: any;
}

export interface WorkerResponse {
  type: 'success' | 'error';
  payload: any;
}

// Worker message handler
self.onmessage = async (e: MessageEvent<WorkerMessage>) => {
  const { type, payload } = e.data;

  try {
    if (type === 'parse') {
      const { content, fileName } = payload;
      
      let transactions: Transaction[];
      let columnMapping: ColumnMapping = {};
      
      // Detect format and parse
      if (fileName.endsWith('.ofx') || isOFX(content)) {
        transactions = parseOFX(content);
      } else if (fileName.endsWith('.qfx') || isQFX(content)) {
        transactions = parseQFX(content);
      } else {
        const parsed = parseCSV(content);
        transactions = parsed.transactions;
        columnMapping = parsed.columnMapping;
      }

      self.postMessage({
        type: 'success',
        payload: { transactions, columnMapping }
      });
    } else if (type === 'categorize') {
      const { transactions, customRules = [] } = payload;
      
      // Apply rules and embeddings (fast, no LLM)
      const categorized = transactions.map((txn: Transaction) => {
        // Try rules first
        const ruleResult = applyRules(txn, customRules);
        if (ruleResult) {
          return {
            ...txn,
            category: ruleResult.category,
            confidence: ruleResult.explanation.confidence,
            source: 'rule',
            explanation: ruleResult.explanation,
            needsReview: false,
          };
        }

        // Try embeddings
        const embeddingResult = matchByEmbedding(txn);
        if (embeddingResult) {
          return {
            ...txn,
            category: embeddingResult.category,
            confidence: embeddingResult.explanation.confidence,
            source: 'embedding',
            explanation: embeddingResult.explanation,
            needsReview: embeddingResult.explanation.confidence < 0.55,
          };
        }

        // Default: uncategorized
        return {
          ...txn,
          category: 'Uncategorized',
          confidence: 0.3,
          source: 'manual',
          needsReview: true,
        };
      });

      self.postMessage({
        type: 'success',
        payload: { transactions: categorized }
      });
    }
  } catch (error: any) {
    self.postMessage({
      type: 'error',
      payload: { message: error.message || 'Worker error' }
    });
  }
};

export {};

