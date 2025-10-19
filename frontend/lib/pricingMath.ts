/**
 * Pricing calculation logic
 * 
 * Pure functions for computing estimates, overage, and discounts.
 * All business logic is centralized here for testing and maintenance.
 */

import { PRICING_TIERS, DISCOUNT_RATES, getAddOnPrice, type TierId } from '@/data/pricing';

export interface PricingInput {
  tier: TierId;
  entities: number;
  txPerEntity: number;
  annual: boolean;
  nonprofit: boolean;
  addOns?: {
    sso?: boolean;
    whiteLabel?: boolean;
    extendedLogs?: boolean;
    prioritySupport?: boolean;
  };
}

export interface PricingBreakdown {
  monthly: number;
  annual: number;
  breakdown: {
    baseFee: number;
    extraEntityFee: number;
    extraEntityCount: number;
    includedTxPerEntity: number;
    overagePerEntity: number;
    totalOverage: number;
    addOnsFee: number;
    subtotal: number;
    annualDiscount: number;
    nonprofitDiscount: number;
    finalMonthly: number;
    finalAnnual: number;
  };
  warning?: 'starter_cap' | 'entity_limit';
  warningMessage?: string;
}

/**
 * Main pricing estimation function
 * Implements all business rules from data/pricing.ts
 */
export function estimatePrice(input: PricingInput): PricingBreakdown {
  const tier = PRICING_TIERS[input.tier];
  
  // Enterprise is custom pricing
  if (input.tier === 'enterprise') {
    return {
      monthly: 0,
      annual: 0,
      breakdown: {
        baseFee: 0,
        extraEntityFee: 0,
        extraEntityCount: 0,
        includedTxPerEntity: 0,
        overagePerEntity: 0,
        totalOverage: 0,
        addOnsFee: 0,
        subtotal: 0,
        annualDiscount: 0,
        nonprofitDiscount: 0,
        finalMonthly: 0,
        finalAnnual: 0,
      },
      warning: undefined,
      warningMessage: 'Enterprise pricing is custom. Contact sales for a quote.',
    };
  }

  // Base fee
  const baseFee = tier.priceMonthly;

  // Extra entities calculation
  const extraEntityCount = Math.max(0, input.entities - tier.entitiesIncluded);
  let extraEntityFee = 0;
  let warning: 'starter_cap' | 'entity_limit' | undefined;
  let warningMessage: string | undefined;

  if (extraEntityCount > 0) {
    if (!tier.addOnsAllowed) {
      // Starter cannot add extra entities
      warning = 'entity_limit';
      warningMessage = 'Starter plan is limited to 1 entity. Upgrade to Team for more entities.';
    } else {
      // Team: $39/mo, Firm: $15/mo
      const pricePerEntity = getAddOnPrice('extra_entity', input.tier);
      extraEntityFee = extraEntityCount * pricePerEntity;
    }
  }

  // Transaction overage calculation (per entity)
  const includedTxPerEntity = tier.txIncludedPerEntity;
  const overagePerEntity = Math.max(0, input.txPerEntity - includedTxPerEntity);
  
  // Check Starter hard cap
  if (input.tier === 'starter' && input.txPerEntity > (tier.txCapPerEntity || Infinity)) {
    warning = 'starter_cap';
    warningMessage = `Starter plan has a hard cap of ${tier.txCapPerEntity} tx/mo per entity. Upgrade to Team for unlimited overage.`;
  }

  // Total overage across all entities
  const totalOverage = overagePerEntity * tier.overagePerTx * input.entities;

  // Add-ons calculation
  let addOnsFee = 0;
  if (input.addOns) {
    if (input.addOns.sso) {
      addOnsFee += getAddOnPrice('sso', input.tier);
    }
    if (input.addOns.whiteLabel) {
      addOnsFee += getAddOnPrice('white_label', input.tier);
    }
    if (input.addOns.extendedLogs) {
      addOnsFee += getAddOnPrice('extended_logs', input.tier);
    }
    if (input.addOns.prioritySupport && input.tier !== 'firm') {
      // Priority support included in Firm+
      addOnsFee += getAddOnPrice('priority_support', input.tier);
    }
  }

  // Subtotal before discounts
  const subtotal = baseFee + extraEntityFee + totalOverage + addOnsFee;

  // Apply discounts (multiplicative, annual first then nonprofit)
  let finalMonthly = subtotal;
  let annualDiscount = 0;
  let nonprofitDiscount = 0;

  if (input.annual) {
    annualDiscount = finalMonthly * DISCOUNT_RATES.annual;
    finalMonthly = finalMonthly * (1 - DISCOUNT_RATES.annual);
  }

  if (input.nonprofit) {
    nonprofitDiscount = finalMonthly * DISCOUNT_RATES.nonprofit;
    finalMonthly = finalMonthly * (1 - DISCOUNT_RATES.nonprofit);
  }

  // Round to 2 decimal places
  finalMonthly = Math.round(finalMonthly * 100) / 100;
  const finalAnnual = Math.round(finalMonthly * 12 * 100) / 100;

  return {
    monthly: finalMonthly,
    annual: finalAnnual,
    breakdown: {
      baseFee,
      extraEntityFee,
      extraEntityCount,
      includedTxPerEntity,
      overagePerEntity,
      totalOverage: Math.round(totalOverage * 100) / 100,
      addOnsFee,
      subtotal: Math.round(subtotal * 100) / 100,
      annualDiscount: Math.round(annualDiscount * 100) / 100,
      nonprofitDiscount: Math.round(nonprofitDiscount * 100) / 100,
      finalMonthly,
      finalAnnual,
    },
    warning,
    warningMessage,
  };
}

/**
 * Compare two tiers for same usage
 * Returns which is cheaper and by how much
 */
export function compareTiers(
  tier1: TierId,
  tier2: TierId,
  entities: number,
  txPerEntity: number,
  annual: boolean = false,
  nonprofit: boolean = false
): {
  cheaper: TierId;
  savings: number;
  tier1Price: number;
  tier2Price: number;
} {
  const price1 = estimatePrice({ tier: tier1, entities, txPerEntity, annual, nonprofit });
  const price2 = estimatePrice({ tier: tier2, entities, txPerEntity, annual, nonprofit });

  const cheaper = price1.monthly < price2.monthly ? tier1 : tier2;
  const savings = Math.abs(price1.monthly - price2.monthly);

  return {
    cheaper,
    savings: Math.round(savings * 100) / 100,
    tier1Price: price1.monthly,
    tier2Price: price2.monthly,
  };
}

/**
 * Calculate breakeven point between two tiers
 * Returns the number of transactions per entity where tier2 becomes cheaper
 */
export function calculateBreakeven(
  tier1: TierId,
  tier2: TierId,
  entities: number
): number | null {
  // Binary search for breakeven point (0 to 50,000 tx)
  let low = 0;
  let high = 50000;
  let breakeven: number | null = null;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const comp = compareTiers(tier1, tier2, entities, mid);

    if (comp.cheaper === tier2) {
      breakeven = mid;
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }

  return breakeven;
}

/**
 * Generate example pricing scenarios
 */
export const PRICING_PRESETS = [
  {
    name: 'Solo 1k tx',
    description: 'Small business, 1 entity, 1,000 tx/mo',
    tier: 'starter' as TierId,
    entities: 1,
    txPerEntity: 1000,
  },
  {
    name: '3 entities × 2k tx',
    description: 'Small team, no overage',
    tier: 'team' as TierId,
    entities: 3,
    txPerEntity: 2000,
  },
  {
    name: '6 entities × 3k tx',
    description: 'Compare Team vs Firm',
    tier: 'team' as TierId,
    entities: 6,
    txPerEntity: 3000,
  },
  {
    name: '10 entities × 8k tx',
    description: 'Medium bookkeeping firm',
    tier: 'firm' as TierId,
    entities: 10,
    txPerEntity: 8000,
  },
];

