/**
 * Pricing calculation tests
 * 
 * Validates all business rules from the specification:
 * - Per-entity limits and overage
 * - Discount stacking (annual then nonprofit)
 * - Starter hard cap warnings
 * - Extra entity pricing
 * - Tier comparisons
 */

import { estimatePrice, compareTiers, calculateBreakeven } from '../lib/pricingMath';
import type { TierId } from '../data/pricing';

describe('Pricing calculations', () => {
  describe('Basic tier pricing', () => {
    test('Case A: Starter 1 entity, 3,000 tx/mo', () => {
      // Base 49 + overage (2,500 × $0.08) = 49 + 200 = 249
      const result = estimatePrice({
        tier: 'starter',
        entities: 1,
        txPerEntity: 3000,
        annual: false,
        nonprofit: false,
      });

      expect(result.monthly).toBe(249);
      expect(result.annual).toBe(249 * 12);
      expect(result.breakdown.baseFee).toBe(49);
      expect(result.breakdown.overagePerEntity).toBe(2500);
      expect(result.breakdown.totalOverage).toBe(200);
    });

    test('Case B: Team 3 entities, 2,000 tx each (no overage), no add-ons', () => {
      // Base 149, no overage
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 2000,
        annual: false,
        nonprofit: false,
      });

      expect(result.monthly).toBe(149);
      expect(result.annual).toBe(149 * 12);
      expect(result.breakdown.baseFee).toBe(149);
      expect(result.breakdown.totalOverage).toBe(0);
    });

    test('Case C: 6 entities × 3,000 tx each → compare Team vs Firm', () => {
      // Team: base 149 + extra entities (3×$39 = 117) = 266
      // Overage: per entity (1,000 × $0.04) × 6 = 240 → total 506
      const teamResult = estimatePrice({
        tier: 'team',
        entities: 6,
        txPerEntity: 3000,
        annual: false,
        nonprofit: false,
      });

      expect(teamResult.monthly).toBe(506);
      expect(teamResult.breakdown.baseFee).toBe(149);
      expect(teamResult.breakdown.extraEntityCount).toBe(3);
      expect(teamResult.breakdown.extraEntityFee).toBe(117);
      expect(teamResult.breakdown.overagePerEntity).toBe(1000);
      expect(teamResult.breakdown.totalOverage).toBe(240);

      // Firm: flat 499 (10 entities included, no overage)
      const firmResult = estimatePrice({
        tier: 'firm',
        entities: 6,
        txPerEntity: 3000,
        annual: false,
        nonprofit: false,
      });

      expect(firmResult.monthly).toBe(499);
      expect(firmResult.breakdown.totalOverage).toBe(0);

      // Firm should be cheaper
      expect(firmResult.monthly).toBeLessThan(teamResult.monthly);
    });
  });

  describe('Discount stacking', () => {
    test('Case D: Discounts stack (annual then nonprofit)', () => {
      // Team monthly 149 → annual −17% = 123.67; then nonprofit −10% = 111.30 (round to cents)
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 2000,
        annual: true,
        nonprofit: true,
      });

      expect(result.monthly).toBeCloseTo(111.3, 1); // Allow 0.1 rounding tolerance
      expect(result.breakdown.subtotal).toBe(149);
      expect(result.breakdown.annualDiscount).toBeCloseTo(25.33, 1); // 149 * 0.17
      expect(result.breakdown.nonprofitDiscount).toBeCloseTo(12.37, 1); // 123.67 * 0.10
    });

    test('Annual discount only', () => {
      const result = estimatePrice({
        tier: 'starter',
        entities: 1,
        txPerEntity: 500,
        annual: true,
        nonprofit: false,
      });

      // 49 * 0.83 = 40.67
      expect(result.monthly).toBeCloseTo(40.67, 2);
      expect(result.breakdown.annualDiscount).toBeCloseTo(8.33, 2);
      expect(result.breakdown.nonprofitDiscount).toBe(0);
    });

    test('Nonprofit discount only', () => {
      const result = estimatePrice({
        tier: 'firm',
        entities: 10,
        txPerEntity: 10000,
        annual: false,
        nonprofit: true,
      });

      // 499 * 0.90 = 449.10
      expect(result.monthly).toBeCloseTo(449.10, 2);
      expect(result.breakdown.annualDiscount).toBe(0);
      expect(result.breakdown.nonprofitDiscount).toBeCloseTo(49.90, 2);
    });
  });

  describe('Warnings and limits', () => {
    test('Case E: Starter hard cap warning at >2000 tx', () => {
      const result = estimatePrice({
        tier: 'starter',
        entities: 1,
        txPerEntity: 2500,
        annual: false,
        nonprofit: false,
      });

      expect(result.warning).toBe('starter_cap');
      expect(result.warningMessage).toContain('hard cap');
      expect(result.warningMessage).toContain('2000');
    });

    test('Starter cannot add extra entities', () => {
      const result = estimatePrice({
        tier: 'starter',
        entities: 2,
        txPerEntity: 500,
        annual: false,
        nonprofit: false,
      });

      expect(result.warning).toBe('entity_limit');
      expect(result.warningMessage).toContain('limited to 1 entity');
      expect(result.breakdown.extraEntityFee).toBe(0);
    });

    test('Starter at exactly 2000 tx (no warning)', () => {
      const result = estimatePrice({
        tier: 'starter',
        entities: 1,
        txPerEntity: 2000,
        annual: false,
        nonprofit: false,
      });

      expect(result.warning).toBeUndefined();
      expect(result.monthly).toBe(49 + (1500 * 0.08)); // 49 + 120 = 169
    });
  });

  describe('Extra entities pricing', () => {
    test('Team extra entities at $39/mo each', () => {
      const result = estimatePrice({
        tier: 'team',
        entities: 5, // 2 extra
        txPerEntity: 2000,
        annual: false,
        nonprofit: false,
      });

      expect(result.breakdown.extraEntityCount).toBe(2);
      expect(result.breakdown.extraEntityFee).toBe(78); // 2 * 39
      expect(result.monthly).toBe(149 + 78); // 227
    });

    test('Firm extra entities at $15/mo each', () => {
      const result = estimatePrice({
        tier: 'firm',
        entities: 12, // 2 extra
        txPerEntity: 10000,
        annual: false,
        nonprofit: false,
      });

      expect(result.breakdown.extraEntityCount).toBe(2);
      expect(result.breakdown.extraEntityFee).toBe(30); // 2 * 15
      expect(result.monthly).toBe(499 + 30); // 529
    });
  });

  describe('Overage calculations', () => {
    test('Team overage at $0.04/tx', () => {
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 3000, // 1000 overage per entity
        annual: false,
        nonprofit: false,
      });

      expect(result.breakdown.overagePerEntity).toBe(1000);
      expect(result.breakdown.totalOverage).toBe(120); // 3 * 1000 * 0.04
      expect(result.monthly).toBe(149 + 120);
    });

    test('Firm overage at $0.02/tx', () => {
      const result = estimatePrice({
        tier: 'firm',
        entities: 10,
        txPerEntity: 12000, // 2000 overage per entity
        annual: false,
        nonprofit: false,
      });

      expect(result.breakdown.overagePerEntity).toBe(2000);
      expect(result.breakdown.totalOverage).toBe(400); // 10 * 2000 * 0.02
      expect(result.monthly).toBe(499 + 400);
    });

    test('No overage when under limit', () => {
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 1500,
        annual: false,
        nonprofit: false,
      });

      expect(result.breakdown.overagePerEntity).toBe(0);
      expect(result.breakdown.totalOverage).toBe(0);
      expect(result.monthly).toBe(149);
    });
  });

  describe('Enterprise pricing', () => {
    test('Enterprise returns custom pricing message', () => {
      const result = estimatePrice({
        tier: 'enterprise',
        entities: 25,
        txPerEntity: 50000,
        annual: false,
        nonprofit: false,
      });

      expect(result.monthly).toBe(0);
      expect(result.annual).toBe(0);
      expect(result.warningMessage).toContain('custom');
      expect(result.warningMessage).toContain('Contact sales');
    });
  });

  describe('Complex scenarios', () => {
    test('Team with extra entities, overage, and discounts', () => {
      // 5 entities, 3000 tx each, annual + nonprofit
      // Base: 149
      // Extra entities: 2 * 39 = 78
      // Overage: 5 * 1000 * 0.04 = 200
      // Subtotal: 427
      // Annual: 427 * 0.83 = 354.41
      // Nonprofit: 354.41 * 0.90 = 318.97
      const result = estimatePrice({
        tier: 'team',
        entities: 5,
        txPerEntity: 3000,
        annual: true,
        nonprofit: true,
      });

      expect(result.breakdown.subtotal).toBe(427);
      expect(result.monthly).toBeCloseTo(318.97, 1);
    });

    test('Firm at high volume stays under overage', () => {
      // 10 entities, 9000 tx each (under 10k limit)
      const result = estimatePrice({
        tier: 'firm',
        entities: 10,
        txPerEntity: 9000,
        annual: false,
        nonprofit: false,
      });

      expect(result.monthly).toBe(499);
      expect(result.breakdown.totalOverage).toBe(0);
    });
  });

  describe('Tier comparisons', () => {
    test('Compare Team vs Firm at 6 entities × 3000 tx', () => {
      const comparison = compareTiers('team', 'firm', 6, 3000);

      expect(comparison.cheaper).toBe('firm');
      expect(comparison.tier1Price).toBe(506);
      expect(comparison.tier2Price).toBe(499);
      expect(comparison.savings).toBe(7);
    });

    test('Compare Starter vs Team at low volume', () => {
      const comparison = compareTiers('starter', 'team', 1, 600);

      // Starter: 49 + (100 * 0.08) = 57
      // Team: 149 (3 entities included, so 1 entity is wasteful)
      expect(comparison.cheaper).toBe('starter');
      expect(comparison.tier1Price).toBe(57);
      expect(comparison.tier2Price).toBe(149);
    });
  });

  describe('Breakeven calculations', () => {
    test('Find breakeven between Starter and Team at 1 entity', () => {
      const breakeven = calculateBreakeven('starter', 'team', 1);

      // Breakeven should be around where Starter overage makes it more expensive
      // Starter base: 49, overage starts at 500 tx at $0.08/tx
      // Team base: 149, included: 2000 tx
      // Need to find where 49 + (x - 500) * 0.08 > 149
      // x > 1750
      expect(breakeven).toBeGreaterThan(1700);
      expect(breakeven).toBeLessThan(1800);
    });
  });

  describe('Edge cases', () => {
    test('Zero transactions', () => {
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 0,
        annual: false,
        nonprofit: false,
      });

      expect(result.monthly).toBe(149);
      expect(result.breakdown.totalOverage).toBe(0);
    });

    test('Very high transaction count', () => {
      const result = estimatePrice({
        tier: 'firm',
        entities: 10,
        txPerEntity: 50000,
        annual: false,
        nonprofit: false,
      });

      // 40,000 overage per entity * 10 entities * $0.02 = 8,000
      expect(result.breakdown.totalOverage).toBe(8000);
      expect(result.monthly).toBe(499 + 8000);
    });

    test('Rounding precision', () => {
      const result = estimatePrice({
        tier: 'team',
        entities: 3,
        txPerEntity: 2001, // 1 tx overage per entity
        annual: false,
        nonprofit: false,
      });

      // 3 * 1 * 0.04 = 0.12
      expect(result.breakdown.totalOverage).toBe(0.12);
      expect(result.monthly).toBe(149.12);
    });
  });
});

