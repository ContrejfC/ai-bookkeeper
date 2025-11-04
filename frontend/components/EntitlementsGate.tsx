/**
 * EntitlementsGate - Route and Feature Access Control
 * ==================================================
 * 
 * This component gates access to premium features based on subscription status
 * and transaction quotas.
 * 
 * Features:
 * --------
 * - Route protection (redirect to /pricing if no access)
 * - Feature disabling (soft limits)
 * - Quota display (usage meters)
 * - Upgrade CTAs
 * 
 * Usage:
 * ------
 * ```tsx
 * // Protect entire route
 * <EntitlementsGate>
 *   <TransactionsPage />
 * </EntitlementsGate>
 * 
 * // Protect specific feature
 * <EntitlementsGate requiredFeature="qbo_export" softBlock>
 *   <Button onClick={exportToQBO}>Export to QBO</Button>
 * </EntitlementsGate>
 * 
 * // Show quota usage
 * <EntitlementsGate showQuota>
 *   ...content...
 * </EntitlementsGate>
 * ```
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardBody, Button, Progress, Chip } from '@nextui-org/react';

export interface Entitlements {
  plan: string;
  status: string;
  entities_allowed: number;
  tx_quota_monthly: number;
  tx_used_monthly: number;
  tx_remaining: number;
  features: string[];
  addons: any[];
}

interface EntitlementsGateProps {
  children: React.ReactNode;
  
  /** Redirect to /pricing if not active */
  requireActive?: boolean;
  
  /** Required feature (e.g., "qbo_export") */
  requiredFeature?: string;
  
  /** Soft block: show message but don't redirect */
  softBlock?: boolean;
  
  /** Show quota usage meter */
  showQuota?: boolean;
  
  /** Custom fallback component */
  fallback?: React.ReactNode;
  
  /** Class name */
  className?: string;
}

/**
 * Fetch entitlements from API
 */
async function fetchEntitlements(): Promise<Entitlements | null> {
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${API_BASE}/api/billing/entitlements`, {
      credentials: 'include',  // Send cookies for authentication
    });
    if (!response.ok) {
      console.error('Entitlements API error:', response.status, response.statusText);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching entitlements:', error);
    return null;
  }
}

/**
 * EntitlementsGate Component
 */
export function EntitlementsGate({
  children,
  requireActive = true,
  requiredFeature,
  softBlock = false,
  showQuota = false,
  fallback,
  className = ''
}: EntitlementsGateProps) {
  const router = useRouter();
  const [entitlements, setEntitlements] = useState<Entitlements | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEntitlements().then((data) => {
      setEntitlements(data);
      setLoading(false);
    });
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-default-500">Checking access...</div>
      </div>
    );
  }

  // Error state - fail gracefully (allow access even if entitlements check fails)
  if (!entitlements) {
    console.warn('EntitlementsGate: Failed to load entitlements, allowing access');
    // Render children without entitlements check (graceful degradation)
    return (
      <div className={className}>
        {children}
      </div>
    );
  }

  // Check if subscription is active
  if (requireActive && entitlements.status !== 'active' && entitlements.plan !== 'free') {
    if (softBlock) {
      return (
        <div className={className}>
          <Card className="border-warning">
            <CardBody className="gap-4">
              <div>
                <h3 className="text-lg font-semibold">Subscription Inactive</h3>
                <p className="text-default-600 mt-2">
                  Your subscription is currently {entitlements.status}. Please update your billing to continue.
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  color="warning"
                  onClick={() => router.push('/firm')}
                >
                  Manage Billing
                </Button>
                <Button
                  variant="flat"
                  onClick={() => router.push('/pricing')}
                >
                  View Plans
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      );
    } else {
      // Hard redirect
      router.push('/pricing');
      return null;
    }
  }

  // Check if required feature is available
  if (requiredFeature && !entitlements.features.includes(requiredFeature)) {
    if (softBlock) {
      return (
        <div className={className}>
          <Card className="border-primary">
            <CardBody className="gap-4">
              <div>
                <h3 className="text-lg font-semibold">Premium Feature</h3>
                <p className="text-default-600 mt-2">
                  This feature requires a {getPlanForFeature(requiredFeature)} plan or higher.
                </p>
                <p className="text-sm text-default-500 mt-1">
                  Current plan: <Chip size="sm">{entitlements.plan}</Chip>
                </p>
              </div>
              <Button
                color="primary"
                onClick={() => router.push('/pricing')}
              >
                Upgrade Plan
              </Button>
            </CardBody>
          </Card>
        </div>
      );
    } else {
      router.push('/pricing');
      return null;
    }
  }

  // Check quota (soft limit - show warning)
  const quotaPercentage = (entitlements.tx_used_monthly / entitlements.tx_quota_monthly) * 100;
  const isNearLimit = quotaPercentage >= 80;
  const isAtLimit = entitlements.tx_remaining <= 0;

  // Hard limit - block access
  if (isAtLimit && requireActive) {
    if (softBlock || fallback) {
      return (
        <>
          {fallback || (
            <div className={className}>
              <Card className="border-danger">
                <CardBody className="gap-4">
                  <div>
                    <h3 className="text-lg font-semibold text-danger">Quota Exceeded</h3>
                    <p className="text-default-600 mt-2">
                      You've used all {entitlements.tx_quota_monthly} transactions this month.
                    </p>
                    <p className="text-sm text-default-500 mt-1">
                      Upgrade to process more transactions or wait until next month.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      color="danger"
                      onClick={() => router.push('/pricing')}
                    >
                      Upgrade Now
                    </Button>
                    <Button
                      variant="flat"
                      onClick={() => router.push('/firm')}
                    >
                      Manage Plan
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
          )}
        </>
      );
    } else {
      router.push('/pricing');
      return null;
    }
  }

  // Render children with optional quota display
  return (
    <div className={className}>
      {showQuota && (
        <Card className="mb-4">
          <CardBody className="gap-2">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium">Monthly Transactions</p>
                <p className="text-xs text-default-500">
                  {entitlements.tx_used_monthly} / {entitlements.tx_quota_monthly === 999999 ? 'Unlimited' : entitlements.tx_quota_monthly}
                </p>
              </div>
              <Chip 
                size="sm" 
                variant="flat"
                color={isAtLimit ? 'danger' : isNearLimit ? 'warning' : 'success'}
              >
                {entitlements.plan}
              </Chip>
            </div>
            
            {entitlements.tx_quota_monthly < 999999 && (
              <Progress
                value={quotaPercentage}
                color={isAtLimit ? 'danger' : isNearLimit ? 'warning' : 'success'}
                size="sm"
                className="w-full"
              />
            )}
            
            {isNearLimit && !isAtLimit && (
              <p className="text-xs text-warning mt-1">
                ⚠️ {entitlements.tx_remaining} transactions remaining
              </p>
            )}
          </CardBody>
        </Card>
      )}
      
      {children}
    </div>
  );
}

/**
 * Hook to access entitlements in any component
 */
export function useEntitlements() {
  const [entitlements, setEntitlements] = useState<Entitlements | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEntitlements().then((data) => {
      setEntitlements(data);
      setLoading(false);
    });
  }, []);

  const refetch = async () => {
    setLoading(true);
    const data = await fetchEntitlements();
    setEntitlements(data);
    setLoading(false);
  };

  return { entitlements, loading, refetch };
}

/**
 * Helper to determine required plan for a feature
 */
function getPlanForFeature(feature: string): string {
  const featurePlanMap: Record<string, string> = {
    'ai_categorization': 'Starter',
    'basic_export': 'Starter',
    'advanced_rules': 'Professional',
    'qbo_export': 'Professional',
    'xero_export': 'Professional',
    'priority_support': 'Enterprise'
  };
  
  return featurePlanMap[feature] || 'Professional';
}

