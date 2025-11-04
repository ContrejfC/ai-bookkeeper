/**
 * Marketing Container Component
 * =============================
 * 
 * Consistent container wrapper matching /pricing design system.
 * Provides max-width, padding, and centering for marketing pages.
 */

import { ReactNode } from 'react';

interface ContainerProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl' | '5xl' | '6xl' | '7xl';
}

const maxWidthClasses = {
  'sm': 'max-w-screen-sm',
  'md': 'max-w-screen-md',
  'lg': 'max-w-screen-lg',
  'xl': 'max-w-screen-xl',
  '2xl': 'max-w-screen-2xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
  '7xl': 'max-w-7xl',
};

export function Container({ 
  children, 
  className = '', 
  maxWidth = '7xl' 
}: ContainerProps) {
  return (
    <div className={`container mx-auto px-4 ${maxWidthClasses[maxWidth]} ${className}`}>
      {children}
    </div>
  );
}

