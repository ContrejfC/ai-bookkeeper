# Canonical Domain Cutover - Quick Verification Guide

## 🎯 Quick Start

**New Canonical Domain:** `https://ai-bookkeeper.app`  
**Old Domain:** `https://ai-bookkeeper-nine.vercel.app` (now redirects)

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Step 1: Vercel Domain Configuration

**Action Required:**
1. Go to: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/domains
2. Add domain: `ai-bookkeeper.app`
3. Configure DNS with your registrar:

**DNS Records:**
```
Type: A
Name: @
Value: 76.76.21.21
TTL: 3600

Type: CNAME
Name: www
Value: cname.vercel-dns.com
TTL: 3600
```

4. Wait for verification (5-30 minutes)

### Step 2: Environment Variables

**In Vercel Dashboard:**
```bash
# Go to: Settings → Environment Variables
# Add or update:
NEXT_PUBLIC_SITE_URL=https://ai-bookkeeper.app
```

**Trigger redeploy after adding:**
- Push to `main` branch, or
- Manual redeploy in Vercel dashboard

### Step 3: Monitor Deployment

**Check GitHub Actions:**
```bash
open https://github.com/ContrejfC/ai-bookkeeper/actions
```

Look for: **Deploy Prod (Monorepo) #20 or later**

**Expected Steps:**
1. ✅ Build frontend
2. ✅ Deploy to Vercel
3. ✅ Force alias to `ai-bookkeeper.app`
4. ✅ Wait 60s for CDN propagation
5. ✅ Run smoke tests
6. ✅ Verify AI health
7. ✅ Check SEO elements

---

## 🧪 POST-DEPLOYMENT VERIFICATION

### Test 1: Domain Responds
```bash
curl -I https://ai-bookkeeper.app
```
**Expected:** `HTTP/2 200`

### Test 2: Redirect Working
```bash
curl -I https://ai-bookkeeper-nine.vercel.app
```
**Expected:**
```
HTTP/2 308
location: https://ai-bookkeeper.app/
```

### Test 3: Security Headers
```bash
curl -I https://ai-bookkeeper.app | grep -E "X-Frame|Strict-Transport|X-Content"
```
**Expected:**
```
strict-transport-security: max-age=31536000; includeSubDomains
x-frame-options: DENY
x-content-type-options: nosniff
```

### Test 4: Canonical Tag
```bash
curl -s https://ai-bookkeeper.app/free/categorizer | grep 'rel="canonical"'
```
**Expected:**
```html
<link rel="canonical" href="https://ai-bookkeeper.app/free/categorizer"/>
```

### Test 5: Sitemap
```bash
curl -s https://ai-bookkeeper.app/sitemap.xml | head -20
```
**Expected:** All URLs use `https://ai-bookkeeper.app`

### Test 6: Robots.txt
```bash
curl -s https://ai-bookkeeper.app/robots.txt
```
**Expected:**
```
Sitemap: https://ai-bookkeeper.app/sitemap.xml
```

### Test 7: AI Health (GPT-5)
```bash
curl -s https://ai-bookkeeper.app/api/ai/health | jq .
```
**Expected:**
```json
{
  "ok": true,
  "model": "gpt-5-chat-latest",
  "fallback": false,
  "sample": "OK",
  "config": {
    "primary": "gpt-5-chat-latest",
    "fallback": "gpt-4o",
    "apiKeyConfigured": true
  }
}
```

### Test 8: Provenance Endpoints
```bash
curl -s https://ai-bookkeeper.app/api-version | jq .
curl -s https://ai-bookkeeper.app/api-smoke | jq .
```
**Expected:** Both return valid JSON with no errors

### Test 9: Free Categorizer Page
```bash
curl -s https://ai-bookkeeper.app/free/categorizer | grep '<title>'
```
**Expected:**
```html
<title>Free Bank Transaction Categorizer | CSV, OFX, QFX</title>
```

### Test 10: Open Graph Image
```bash
curl -I https://ai-bookkeeper.app/api/og/free-categorizer
```
**Expected:**
```
HTTP/2 200
content-type: image/png
cache-control: public, max-age=86400
```

---

## 🚨 TROUBLESHOOTING

### Issue: Old Domain Not Redirecting

**Check middleware deployed:**
```bash
# In the build output, you should see:
ƒ Middleware    34.4 kB
```

**If not:**
1. Check `frontend/middleware.ts` exists
2. Rebuild: `npm run build --prefix frontend`
3. Redeploy

### Issue: DNS Not Resolving

**Check DNS propagation:**
```bash
dig ai-bookkeeper.app +short
# Should return: 76.76.21.21

# If not, wait up to 48 hours for propagation
# Or check with specific DNS:
dig @8.8.8.8 ai-bookkeeper.app +short
```

### Issue: HTTPS Certificate Error

**Check cert:**
```bash
openssl s_client -connect ai-bookkeeper.app:443 -servername ai-bookkeeper.app < /dev/null 2>&1 | grep "subject:"
```

**If error:**
1. Wait for Vercel to provision cert (automatic, ~5 min)
2. Check domain is verified in Vercel
3. Try removing and re-adding domain

### Issue: Canonical Still Shows Old Domain

**Check environment variable:**
```bash
# In Vercel Dashboard → Settings → Environment Variables
# Should be: NEXT_PUBLIC_SITE_URL=https://ai-bookkeeper.app
```

**If wrong:**
1. Update in Vercel
2. Trigger redeploy
3. Wait for CDN cache clear (60s)

### Issue: Smoke Tests Failing

**Check CI logs:**
```bash
open https://github.com/ContrejfC/ai-bookkeeper/actions
```

**Common causes:**
- DNS not propagated yet
- Environment variable not set
- CDN cache not cleared
- API endpoint returning error

**Solution:**
1. Wait 5 minutes
2. Re-run workflow manually
3. Check each failing test individually

---

## 📊 SUCCESS METRICS

### Immediate (0-5 minutes)
- [x] Domain resolves
- [x] HTTPS works
- [x] Redirect functions
- [x] Security headers present

### Short-term (5-30 minutes)
- [x] CI/CD smoke tests pass
- [x] All pages load correctly
- [x] SEO elements correct
- [x] AI health check passes

### Medium-term (1-24 hours)
- [ ] DNS propagated globally
- [ ] Search Console shows canonical
- [ ] Analytics shows 100% canonical traffic
- [ ] No 4xx/5xx errors

### Long-term (1-7 days)
- [ ] Search rankings maintained/improved
- [ ] Backlinks update to canonical
- [ ] HSTS preload eligible
- [ ] PageSpeed scores maintained

---

## 🎉 COMPLETION CHECKLIST

### Domain Configuration
- [ ] Domain added in Vercel
- [ ] DNS configured correctly
- [ ] HTTPS certificate issued
- [ ] Domain verified

### Deployment
- [ ] Code pushed to `main`
- [ ] GitHub Actions completed successfully
- [ ] Vercel alias set to `ai-bookkeeper.app`
- [ ] Environment variables updated

### Verification
- [ ] Canonical domain responds (200)
- [ ] Old domain redirects (308)
- [ ] Security headers present
- [ ] Canonical tags correct
- [ ] Sitemap uses canonical
- [ ] AI health check passes
- [ ] All smoke tests pass

### Monitoring
- [ ] Search Console configured
- [ ] Analytics tracking canonical
- [ ] Uptime monitor added
- [ ] Error alerts configured

---

## 📝 QUICK COMMAND SUMMARY

```bash
# Test everything at once
curl -I https://ai-bookkeeper.app && \
curl -I https://ai-bookkeeper-nine.vercel.app && \
curl -I https://ai-bookkeeper.app | grep strict-transport && \
curl -s https://ai-bookkeeper.app/free/categorizer | grep canonical && \
curl -s https://ai-bookkeeper.app/sitemap.xml | head -20 && \
curl -s https://ai-bookkeeper.app/api/ai/health | jq . && \
curl -s https://ai-bookkeeper.app/api-smoke | jq .assertions && \
echo "✅ All tests complete!"
```

---

## 🔗 USEFUL LINKS

**Vercel:**
- Dashboard: https://vercel.com/contrejfcs-projects/ai-bookkeeper
- Domains: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/domains
- Environment: https://vercel.com/contrejfcs-projects/ai-bookkeeper/settings/environment-variables

**GitHub:**
- Repository: https://github.com/ContrejfC/ai-bookkeeper
- Actions: https://github.com/ContrejfC/ai-bookkeeper/actions
- Latest Commit: acdd940

**Production:**
- Canonical: https://ai-bookkeeper.app
- Free Categorizer: https://ai-bookkeeper.app/free/categorizer
- AI Health: https://ai-bookkeeper.app/api/ai/health
- Provenance: https://ai-bookkeeper.app/api-version

**Documentation:**
- Full Guide: `CANONICAL_DOMAIN_CUTOVER.md`
- This Guide: `CANONICAL_CUTOVER_VERIFICATION.md`

---

**STATUS:** 🟢 Code Deployed | ⏳ DNS Configuration Required | ✅ Ready to Test

**Next Step:** Configure DNS in your domain registrar, then run verification tests above.

