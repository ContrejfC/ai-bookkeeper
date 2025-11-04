# .env.example Updates Required

## Manual Update Needed

The file `ops/launch_checks/.env.example` is filtered by `.cursorignore` and cannot be edited directly. Please manually add the following line to the file:

### Add to Stripe Section

After the `STRIPE_WEBHOOK_SECRET` line, add:

```bash
# App webhook endpoint (public URL)
WEBHOOK_URL=https://<api-base>/api/webhooks/stripe
```

### Complete Stripe Section Should Look Like:

```bash
# ============================================================================
# OPTIONAL - Stripe Integration (if not set, Stripe checks skip)
# ============================================================================

# Stripe test secret key (starts with sk_test_)
STRIPE_SECRET_KEY=sk_test_51234567890abcdef

# Stripe webhook secret (starts with whsec_)
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef

# App webhook endpoint (public URL)
WEBHOOK_URL=https://<api-base>/api/webhooks/stripe
```

## Why This Change?

The `WEBHOOK_URL` variable is used by webhook idempotency checks to test that duplicate webhook events are properly handled. This ensures your API doesn't process the same Stripe event multiple times.

## Verification

After updating, verify the variable is documented:

```bash
grep WEBHOOK_URL ops/launch_checks/.env.example
```

Expected output:
```
# App webhook endpoint (public URL)
WEBHOOK_URL=https://<api-base>/api/webhooks/stripe
```

---

**Note:** The file was renamed from `env.example` to `.env.example` to follow standard naming conventions.



