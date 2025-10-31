'use client';

/**
 * CategoryFeedback Component
 * 
 * Shows interactive questions for low-confidence transactions.
 * Captures user feedback to improve categorization model.
 */

import React, { useState } from 'react';

interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
  confidence: number;
  suggested_categories?: string[];
}

interface CategoryFeedbackProps {
  transaction: Transaction;
  onFeedback: (transactionId: string, selectedCategory: string) => void;
  onSkip: (transactionId: string) => void;
}

export function CategoryFeedback({ transaction, onFeedback, onSkip }: CategoryFeedbackProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customCategory, setCustomCategory] = useState('');

  const handleSubmit = () => {
    const category = showCustomInput ? customCategory : selectedCategory;
    if (category) {
      onFeedback(transaction.id, category);
    }
  };

  // Default suggested categories if none provided
  const suggestedCategories = transaction.suggested_categories || [
    transaction.category,
    'Business Expenses',
    'Personal',
    'Travel',
    'Food & Dining',
    'Shopping',
    'Entertainment',
    'Bills & Utilities',
    'Healthcare',
    'Other'
  ];

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-4">
      {/* Question Header */}
      <div className="flex items-start gap-3 mb-4">
        <span className="text-3xl">🤔</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Help us categorize this transaction
          </h3>
          <p className="text-sm text-gray-600">
            We're not sure about this one. Your feedback helps improve accuracy!
          </p>
        </div>
      </div>

      {/* Transaction Details */}
      <div className="bg-white rounded-lg p-4 mb-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Date:</span>
            <span className="ml-2 font-medium">{transaction.date}</span>
          </div>
          <div>
            <span className="text-gray-500">Amount:</span>
            <span className={`ml-2 font-medium ${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
              ${Math.abs(transaction.amount).toFixed(2)}
            </span>
          </div>
        </div>
        <div className="mt-2">
          <span className="text-gray-500 text-sm">Description:</span>
          <p className="font-medium text-gray-900 mt-1">{transaction.description}</p>
        </div>
      </div>

      {/* AI Suggestion */}
      <div className="mb-4">
        <p className="text-sm text-gray-700 mb-3">
          Our AI suggests: <span className="font-semibold">{transaction.category}</span>
          <span className="ml-2 text-xs text-gray-500">
            (Confidence: {(transaction.confidence * 100).toFixed(0)}%)
          </span>
        </p>
      </div>

      {/* Category Options */}
      {!showCustomInput ? (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-3">
            What category should this be?
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4">
            {suggestedCategories.slice(0, 9).map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`
                  px-4 py-2 text-sm font-medium rounded-lg border transition-colors
                  ${selectedCategory === cat
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                  }
                `}
              >
                {cat}
              </button>
            ))}
          </div>
          
          <button
            onClick={() => setShowCustomInput(true)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            + Enter custom category
          </button>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Custom Category:
          </label>
          <input
            type="text"
            value={customCategory}
            onChange={(e) => setCustomCategory(e.target.value)}
            placeholder="e.g., Office Supplies"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            autoFocus
          />
          <button
            onClick={() => setShowCustomInput(false)}
            className="mt-2 text-sm text-gray-600 hover:text-gray-700"
          >
            ← Back to suggestions
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6">
        <button
          onClick={handleSubmit}
          disabled={!selectedCategory && !customCategory}
          className={`
            flex-1 px-6 py-3 font-semibold rounded-lg transition-colors
            ${selectedCategory || customCategory
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Submit Category
        </button>
        
        <button
          onClick={() => onSkip(transaction.id)}
          className="px-6 py-3 text-gray-600 font-medium hover:text-gray-900 transition-colors"
        >
          Skip
        </button>
      </div>

      {/* Confidence Indicator */}
      <div className="mt-4 pt-4 border-t border-yellow-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>AI Confidence</span>
          <span>{(transaction.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              transaction.confidence >= 0.7 ? 'bg-yellow-500' :
              transaction.confidence >= 0.5 ? 'bg-orange-500' :
              'bg-red-500'
            }`}
            style={{ width: `${transaction.confidence * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * FeedbackSummary Component
 * 
 * Shows summary after user provides feedback
 */
interface FeedbackSummaryProps {
  totalTransactions: number;
  feedbackProvided: number;
  onContinue: () => void;
}

export function FeedbackSummary({ totalTransactions, feedbackProvided, onContinue }: FeedbackSummaryProps) {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
      <div className="flex items-start gap-3">
        <span className="text-3xl">✅</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Thank you for your feedback!
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            You helped categorize {feedbackProvided} transaction{feedbackProvided !== 1 ? 's' : ''}.
            This data will improve our AI for everyone.
          </p>
          
          <div className="bg-white rounded-lg p-4 mb-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">Feedback provided:</span>
              <span className="font-semibold text-green-600">
                {feedbackProvided} / {totalTransactions} transactions
              </span>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{ width: `${(feedbackProvided / totalTransactions) * 100}%` }}
              />
            </div>
          </div>

          <button
            onClick={onContinue}
            className="w-full px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
          >
            Continue to Download
          </button>
        </div>
      </div>
    </div>
  );
}

