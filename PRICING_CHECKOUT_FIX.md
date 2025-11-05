# Pricing Page Checkout Error - Quick Fix

## 🔴 Issue

**Error:** "Failed to start checkout. Please try again."

**Cause:** The pricing page is trying to connect to the backend API for Stripe checkout, but `NEXT_PUBLIC_API_URL` is either:
1. Not set in Vercel environment variables, OR
2. Set to a backend that's not responding

---

## ✅ QUICK FIX

### Option 1: Set Backend API URL (If You Have a Backend)

**In Vercel:**
1. Go to: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/environment-variables
2. Add or update:
   ```
   NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
   ```
   (Or whatever your backend API URL is)
3. Check "Production"
4. Click "Save"
5. Redeploy

### Option 2: Disable Checkout Until Backend is Ready

**Update the pricing page to show a "coming soon" message:**

Edit `frontend/app/pricing/page.tsx`:

```typescript
const handleCheckout = async (planId: string) => {
  const term = annual ? 'annual' : 'monthly';
  trackCheckoutClicked(planId, term);

  // Temporary: Backend not deployed yet
  alert('Checkout coming soon! Please contact sales@ai-bookkeeper.app for early access.');
  return;
  
  // Original code (comment out for now):
  // try {
  //   const response = await fetch(...);
  // ...
};
```

---

## 🔍 What's Happening

**Current flow:**
1. User clicks "Start Starter" (or Team/Firm)
2. Frontend tries: `POST https://[empty]/api/billing/checkout`
3. Request fails (no host)
4. Shows alert: "Failed to start checkout"

**Backend Status:**
- The backend API is deployed at: https://api.ai-bookkeeper.app
- But the frontend doesn't know where to find it
- Need to set `NEXT_PUBLIC_API_URL` in Vercel

---

## 📋 CHECK BACKEND STATUS

**Test if backend is live:**
```bash
curl -I https://api.ai-bookkeeper.app/healthz
```

**If returns 200:**
- Backend is working ✅
- Just need to set NEXT_PUBLIC_API_URL in Vercel

**If returns 404 or fails:**
- Backend might not be deployed yet
- Use Option 2 above (disable checkout temporarily)

---

## 🚀 RECOMMENDED FIX

**Add to Vercel environment variables:**

```bash
NEXT_PUBLIC_API_URL=https://api.ai-bookkeeper.app
```

**Then redeploy.**

This will fix the checkout flow and connect the frontend to your backend API.

---

**Quick check - what's your backend API URL?** 

If you're not sure or it's not deployed yet, I can help you disable the checkout buttons temporarily with a "Contact Sales" message instead.

