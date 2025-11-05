/**
 * Transaction Schema
 * ===================
 * Normalized transaction type for all parsers (CSV, OFX, QFX)
 */

export interface Transaction {
  // Core fields
  id: string;                    // Unique ID (generated)
  date: Date;                    // Transaction date
  description: string;           // Merchant/description
  amount: number;                // Signed amount (negative = debit, positive = credit)
  
  // Optional fields
  currency?: string;             // USD, EUR, etc.
  category?: string;             // Assigned category
  payee?: string;                // Extracted payee name
  
  // Metadata
  confidence?: number;           // 0.0-1.0 confidence score
  needsReview?: boolean;         // True if confidence < threshold
  duplicate?: boolean;           // True if likely duplicate
  source?: 'rule' | 'embedding' | 'llm' | 'manual'; // How it was categorized
  explanation?: Explanation;     // Why this category was chosen
  
  // Original data
  rawDescription?: string;       // Original before normalization
  rawAmount?: string;            // Original amount string
  originalIndex?: number;        // Original row number
}

export interface Explanation {
  stage: 'rule' | 'embedding' | 'llm';
  confidence: number;
  
  // Rule-based
  ruleId?: string;
  ruleName?: string;
  
  // Embedding-based
  topMatch?: string;
  similarity?: number;
  
  // LLM-based
  llmHint?: string;
  llmModel?: string;
  
  // Performance
  pipelineTimeMs?: number;
}

export interface ColumnMapping {
  date?: number;              // Column index for date
  description?: number;       // Column index for description
  amount?: number;            // Column index for amount
  debit?: number;             // Column index for debit (alternative to amount)
  credit?: number;            // Column index for credit
  payee?: number;             // Column index for payee
  category?: number;          // Column index for existing category
}

export interface ParsedData {
  transactions: Transaction[];
  columnMapping: ColumnMapping;
  rowCount: number;
  dateFormat?: string;
  currency?: string;
  duplicateCount: number;
}

export interface CSVRow {
  [key: string]: string;
}

