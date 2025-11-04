/**
 * Page Hero Component
 * ===================
 * 
 * Hero section matching /pricing design system.
 * Supports title, subtitle, badges, CTAs, and trust indicators.
 */

import { ReactNode } from 'react';

interface PageHeroProps {
  title: string;
  subtitle?: string;
  badge?: ReactNode;
  children?: ReactNode;
  trustStrip?: ReactNode;
  className?: string;
}

export function PageHero({ 
  title, 
  subtitle, 
  badge,
  children, 
  trustStrip,
  className = '' 
}: PageHeroProps) {
  return (
    <div className={`text-center mb-12 ${className}`}>
      {badge && (
        <div className="mb-4 flex justify-center">
          {badge}
        </div>
      )}
      
      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
        {title}
      </h1>
      
      {subtitle && (
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
          {subtitle}
        </p>
      )}
      
      {children}
      
      {trustStrip && (
        <div className="mt-8 flex flex-wrap justify-center items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
          {trustStrip}
        </div>
      )}
    </div>
  );
}

