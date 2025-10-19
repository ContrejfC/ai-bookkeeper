/**
 * Pricing configuration - Single source of truth
 * 
 * All pricing logic, tiers, add-ons, and business rules are defined here.
 * To modify pricing:
 * 1. Update tier prices/limits in PRICING_TIERS
 * 2. Update add-on prices in ADD_ONS
 * 3. Adjust discount rates in DISCOUNT_RATES
 * 4. Run tests to verify calculations
 */

export type TierId = 'starter' | 'team' | 'firm' | 'enterprise';
export type BillingCycle = 'monthly' | 'annual';
export type AddOnId = 'extra_entity' | 'sso' | 'white_label' | 'extended_logs' | 'priority_support';

export interface Tier {
  id: TierId;
  name: string;
  badge?: string;
  priceMonthly: number; // base price / mo
  entitiesIncluded: number;
  entitiesMax: number; // max entities including add-ons (0 = unlimited)
  txIncludedPerEntity: number;
  txCapPerEntity?: number; // hard cap (e.g., Starter 2000)
  overagePerTx: number; // $/tx
  features: string[];
  notes?: string[];
  addOnsAllowed?: boolean;
  popular?: boolean;
}

export interface AddOn {
  id: AddOnId;
  name: string;
  description: string;
  priceMonthly: number;
  availability: Array<TierId | 'all'>;
  priceByTier?: Partial<Record<TierId, number>>; // different prices per tier
}

export const PRICING_TIERS: Record<TierId, Tier> = {
  starter: {
    id: 'starter',
    name: 'Starter',
    badge: 'Best for SMBs',
    priceMonthly: 49,
    entitiesIncluded: 1,
    entitiesMax: 1, // cannot add extra entities
    txIncludedPerEntity: 500,
    txCapPerEntity: 2000, // hard cap
    overagePerTx: 0.08,
    features: [
      'OCR + bounding boxes',
      'Propose, review & approve',
      'Export to QuickBooks & Xero',
      'Email support',
      'Rule-based automation',
      'Vendor pattern detection',
    ],
    notes: [
      'Perfect for solo entrepreneurs and small businesses',
      'Hard cap at 2,000 tx/mo per entity',
    ],
    addOnsAllowed: false,
  },
  team: {
    id: 'team',
    name: 'Team',
    badge: 'Teams & small firms',
    priceMonthly: 149,
    entitiesIncluded: 3,
    entitiesMax: 0, // unlimited with add-ons
    txIncludedPerEntity: 2000,
    overagePerTx: 0.04,
    features: [
      'Everything in Starter',
      'Rules versioning & rollback',
      'Bulk approve workflows',
      'Email ingest (receipts)',
      'Priority email support',
      'Multi-user collaboration',
      'Activity audit log (6 months)',
    ],
    notes: [
      'Ideal for small accounting teams',
      'Add extra entities at $39/mo each',
    ],
    addOnsAllowed: true,
    popular: true,
  },
  firm: {
    id: 'firm',
    name: 'Firm',
    badge: 'Bookkeeping firms',
    priceMonthly: 499,
    entitiesIncluded: 10,
    entitiesMax: 0, // unlimited with add-ons
    txIncludedPerEntity: 10000,
    overagePerTx: 0.02,
    features: [
      'Everything in Team',
      'API access (with rate limits)',
      'Full audit export (CSV/JSON)',
      'Role-based access control (RBAC)',
      'Quarterly business review',
      '99.5% uptime SLA',
      'Activity audit log (12 months)',
      'Priority support included',
    ],
    notes: [
      'Designed for professional bookkeeping firms',
      'Add extra entities at $15/mo each',
    ],
    addOnsAllowed: true,
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    badge: 'Compliance-heavy',
    priceMonthly: 0, // custom pricing
    entitiesIncluded: 25,
    entitiesMax: 0, // unlimited
    txIncludedPerEntity: 0, // custom bands
    overagePerTx: 0.01, // floor rate
    features: [
      'Everything in Firm',
      'Custom transaction bands',
      'Pooled pricing across entities',
      'SSO (SAML) included',
      'Custom DPA & MSA',
      'Custom data retention',
      '99.9% uptime SLA',
      'Dedicated success manager',
      'Custom integrations',
      'White-label options',
    ],
    notes: [
      'For large firms and enterprises',
      'Custom pricing and volume discounts',
      'Contact sales for quote',
    ],
    addOnsAllowed: true,
  },
};

export const ADD_ONS: Record<AddOnId, AddOn> = {
  extra_entity: {
    id: 'extra_entity',
    name: 'Extra Entity',
    description: 'Add additional entities to your plan',
    priceMonthly: 39, // default (Team price)
    availability: ['team', 'firm', 'enterprise'],
    priceByTier: {
      team: 39,
      firm: 15,
      enterprise: 0, // custom
    },
  },
  sso: {
    id: 'sso',
    name: 'SSO (SAML)',
    description: 'Single Sign-On with SAML 2.0',
    priceMonthly: 99,
    availability: ['team', 'firm'], // included in enterprise
  },
  white_label: {
    id: 'white_label',
    name: 'White-label',
    description: 'Custom branding and domain',
    priceMonthly: 149,
    availability: ['firm', 'enterprise'],
  },
  extended_logs: {
    id: 'extended_logs',
    name: 'Extended Log Retention',
    description: 'Extend audit logs from 12 to 24 months',
    priceMonthly: 49,
    availability: ['team', 'firm'],
  },
  priority_support: {
    id: 'priority_support',
    name: 'Priority Support',
    description: '24-hour response target',
    priceMonthly: 99,
    availability: ['starter', 'team'], // included in firm+
  },
};

export const DISCOUNT_RATES = {
  annual: 0.17, // 17% discount for annual billing
  nonprofit: 0.10, // 10% discount for nonprofit orgs
};

export const BILLING_RULES = [
  'Billable transaction = a unique bank/CC line ingested and processed through propose. Idempotent retries & re-exports are not billed.',
  'Included transactions are per entity (not pooled). Overage is billed per entity at the tier\'s rate.',
  'Monthly quota resets on calendar month start. Overage is billed at month-end.',
  'Annual prepay discount: −17%. Nonprofit discount: −10%.',
  'Discounts stack multiplicatively: annual discount applied first, then nonprofit discount.',
  'Starter tier has a hard cap of 2,000 tx/mo per entity. Exceeding this requires an upgrade.',
  'Team and Firm tiers allow unlimited overage at the per-transaction rate.',
  'Enterprise pricing is custom and includes volume discounts. Contact sales for a quote.',
];

export const FAQS = [
  {
    question: 'What counts as a billable transaction?',
    answer: 'A billable transaction is a unique bank or credit card line item that is ingested and processed through our AI proposal engine. Idempotent retries, re-exports to QuickBooks/Xero, and manual edits do not count as additional transactions.',
  },
  {
    question: 'Are transaction limits per entity or pooled?',
    answer: 'Transaction limits are per entity, not pooled. For example, on the Team plan with 3 entities, each entity gets 2,000 included transactions per month (6,000 total). Overage is calculated per entity.',
  },
  {
    question: 'When are overages billed?',
    answer: 'Monthly quotas reset on the 1st of each calendar month. Overage charges are calculated at month-end and added to your next invoice. You\'ll receive a warning email when you reach 80% and 100% of your included transactions.',
  },
  {
    question: 'How do discounts stack?',
    answer: 'Discounts are applied multiplicatively in this order: (1) Annual billing discount (−17%), (2) Nonprofit discount (−10%). For example, a $149/mo plan with both discounts: $149 × 0.83 (annual) = $123.67, then × 0.90 (nonprofit) = $111.30/mo.',
  },
  {
    question: 'What happens if I exceed the Starter hard cap?',
    answer: 'The Starter plan has a hard cap of 2,000 transactions per month per entity. If you consistently approach or exceed this limit, you\'ll be prompted to upgrade to the Team plan, which includes 2,000 tx/mo with unlimited overage at $0.04/tx.',
  },
  {
    question: 'Can I change my plan mid-month?',
    answer: 'Yes. Upgrades take effect immediately with prorated billing. Downgrades take effect at the start of your next billing cycle to avoid data loss.',
  },
  {
    question: 'Is my data safe if I don\'t have an active plan?',
    answer: 'Yes. Your data is read-only and fully retained for 90 days after plan cancellation. You can export all data during this period. After 90 days, data is permanently deleted per our retention policy.',
  },
  {
    question: 'Do you offer refunds?',
    answer: 'We offer a 14-day money-back guarantee for first-time annual subscriptions. Monthly plans can be cancelled anytime with no refund for the current month. Enterprise contracts follow custom terms.',
  },
];

/**
 * Helper: Get add-on price for a specific tier
 */
export function getAddOnPrice(addOnId: AddOnId, tierId: TierId): number {
  const addOn = ADD_ONS[addOnId];
  if (addOn.priceByTier && tierId in addOn.priceByTier) {
    return addOn.priceByTier[tierId]!;
  }
  return addOn.priceMonthly;
}

/**
 * Helper: Check if add-on is available for tier
 */
export function isAddOnAvailable(addOnId: AddOnId, tierId: TierId): boolean {
  const addOn = ADD_ONS[addOnId];
  return addOn.availability.includes('all') || addOn.availability.includes(tierId);
}

/**
 * Helper: Get tier by ID with type safety
 */
export function getTier(tierId: TierId): Tier {
  return PRICING_TIERS[tierId];
}

