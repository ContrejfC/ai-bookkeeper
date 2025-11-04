/**
 * Marketing Badge Component
 * ==========================
 * 
 * Small badge/pill component matching /pricing style.
 * Used for labels, status indicators, and feature tags.
 */

import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'info' | 'purple';
  className?: string;
}

const variantClasses = {
  'default': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  'success': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  'warning': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  'info': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'purple': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
};

export function Badge({ 
  children, 
  variant = 'default', 
  className = '' 
}: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
}

