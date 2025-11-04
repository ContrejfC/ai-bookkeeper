/**
 * Marketing Section Component
 * ============================
 * 
 * Full-width section wrapper with consistent spacing.
 * Matches /pricing vertical rhythm and background patterns.
 */

import { ReactNode } from 'react';

interface SectionProps {
  children: ReactNode;
  className?: string;
  background?: 'white' | 'gray' | 'gradient';
  spacing?: 'sm' | 'md' | 'lg' | 'xl';
}

const backgroundClasses = {
  'white': 'bg-white dark:bg-gray-900',
  'gray': 'bg-gray-50 dark:bg-gray-800',
  'gradient': 'bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800',
};

const spacingClasses = {
  'sm': 'py-8',
  'md': 'py-12',
  'lg': 'py-16',
  'xl': 'py-24',
};

export function Section({ 
  children, 
  className = '', 
  background = 'white',
  spacing = 'lg'
}: SectionProps) {
  return (
    <section className={`${backgroundClasses[background]} ${spacingClasses[spacing]} ${className}`}>
      {children}
    </section>
  );
}

