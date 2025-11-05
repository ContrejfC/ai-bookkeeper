'use client';

/**
 * Inline Category Select
 * ========================
 * Typeahead category selector with recent picks from localStorage
 */

import { useState, useEffect, useRef } from 'react';
import { getCategoryNames } from '@/lib/categories';

interface InlineCategorySelectProps {
  value: string;
  onChange: (category: string) => void;
  merchant?: string;
}

const RECENT_KEY = 'cat_recent_merchant_categories';
const MAX_RECENT = 20;

export function InlineCategorySelect({ value, onChange, merchant }: InlineCategorySelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [recentPicks, setRecentPicks] = useState<Record<string, string>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  const categories = getCategoryNames();

  // Load recent picks from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_KEY);
      if (stored) {
        setRecentPicks(JSON.parse(stored));
      }
    } catch (e) {
      console.warn('Failed to load recent categories:', e);
    }
  }, []);

  // Save recent pick
  const saveRecentPick = (merchant: string, category: string) => {
    try {
      const updated = { ...recentPicks, [merchant.toLowerCase()]: category };
      
      // Keep only last 20
      const entries = Object.entries(updated);
      const trimmed = Object.fromEntries(entries.slice(-MAX_RECENT));
      
      localStorage.setItem(RECENT_KEY, JSON.stringify(trimmed));
      setRecentPicks(trimmed);
    } catch (e) {
      console.warn('Failed to save recent category:', e);
    }
  };

  const handleSelect = (category: string) => {
    onChange(category);
    if (merchant) {
      saveRecentPick(merchant, category);
    }
    setIsOpen(false);
    setSearch('');
  };

  // Filter categories by search
  const filtered = search
    ? categories.filter(c => c.toLowerCase().includes(search.toLowerCase()))
    : categories;

  // Prefill from recent if merchant matches
  const suggestedCategory = merchant ? recentPicks[merchant.toLowerCase()] : null;

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value || ''}
        onChange={(e) => setSearch(e.target.value)}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        placeholder="Select category..."
        className="w-full px-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
      />

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border rounded-md shadow-lg max-h-60 overflow-auto">
          {suggestedCategory && !search && (
            <div
              onClick={() => handleSelect(suggestedCategory)}
              className="px-3 py-2 hover:bg-emerald-50 cursor-pointer border-b text-sm font-medium text-emerald-700"
            >
              ⭐ {suggestedCategory} (recent)
            </div>
          )}
          
          {filtered.map(cat => (
            <div
              key={cat}
              onClick={() => handleSelect(cat)}
              className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer text-sm"
            >
              {cat}
            </div>
          ))}
          
          {filtered.length === 0 && (
            <div className="px-3 py-2 text-sm text-gray-500">
              No categories match "{search}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}

