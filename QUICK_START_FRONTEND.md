# Quick Start: AI Bookkeeper Frontend

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Ensure you have Node.js 20+
node --version

# Ensure backend is running on http://localhost:8000
curl http://localhost:8000/healthz
```

### 2. Install & Run
```bash
cd frontend

# Install dependencies (one time)
npm install

# Start development server
npm run dev
```

### 3. Access the App
Open your browser to: **http://localhost:3000**

### 4. Login (Dev Mode)
1. Go to http://localhost:3000/login
2. Click "🔑 Dev Magic Link Login"
3. You'll be logged in as `admin@example.com`

---

## 📱 Available Pages

Once logged in, you can access:

| Page | URL | Description |
|------|-----|-------------|
| **Dashboard** | `/` | Key metrics and recent activity |
| **Transactions** | `/transactions` | Review and approve transactions |
| **Receipts** | `/receipts` | OCR-processed receipts |
| **Rules** | `/rules` | Automation rule candidates |
| **Vendors** | `/vendors` | Vendor patterns and stats |
| **Firm Settings** | `/firm` | Tenant management (owner only) |
| **Audit** | `/audit` | Export audit logs as CSV |
| **Analytics** | `/analytics` | Performance metrics |
| **Export** | `/export` | Export to QBO/Xero |

---

## 🔧 Configuration

### Environment Variables

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Dev vs Production

**Development Mode:**
- Magic link login enabled
- Hot reload active
- Detailed error messages

**Production Mode:**
- Set `NODE_ENV=production`
- Build with `npm run build`
- Start with `npm start`
- Magic link disabled

---

## 🎨 Features

### Authentication
- ✅ JWT cookie-based auth
- ✅ Protected routes
- ✅ Auto-redirect on logout
- ✅ Dev magic link for testing

### UI/UX
- ✅ Dark mode by default
- ✅ Light/dark toggle
- ✅ Responsive design
- ✅ Modern NextUI components
- ✅ Accessible (WCAG AA)

### Data Integration
- ✅ All backend APIs connected
- ✅ Real-time data updates
- ✅ Error handling
- ✅ Loading states

---

## 🛠️ Development

### Run Dev Server
```bash
npm run dev
# Access: http://localhost:3000
```

### Build for Production
```bash
npm run build
npm start
# Access: http://localhost:3000
```

### Linting
```bash
npm run lint
```

---

## 🐛 Troubleshooting

### "Cannot connect to backend"
- Ensure backend is running: `curl http://localhost:8000/healthz`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`

### "Page not found"
- Clear Next.js cache: `rm -rf .next`
- Rebuild: `npm run build`

### "Auth not working"
- Clear cookies in browser
- Try dev magic link login
- Check backend JWT secret is set

### "Build errors"
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Next.js cache: `rm -rf .next`

---

## 📚 User Roles

### Owner Role
- Full access to all tenants
- Can edit tenant settings
- Can approve/reject rules
- Can export data

### Staff Role
- Limited to assigned tenants
- Read-only on settings
- Can review transactions
- Can view reports

---

## 🎯 Next Steps

1. **Try the Demo:**
   - Login with dev magic link
   - Explore all pages
   - Try creating a rule candidate
   - Run a dry-run simulation
   - Export an audit CSV

2. **Connect to Real Data:**
   - Ensure backend has demo data
   - Check transactions endpoint
   - Verify tenant settings
   - Test rule candidates

3. **Customize:**
   - Update branding/colors
   - Add your logo
   - Configure theme
   - Customize navigation

---

## 📖 Documentation

- **Frontend README:** `frontend/README.md`
- **API Client:** `frontend/lib/api.ts`
- **Auth Context:** `frontend/contexts/auth-context.tsx`
- **Full Summary:** `FRONTEND_SUMMARY.md`

---

## ✅ Health Check

Verify everything is working:

```bash
# 1. Check backend
curl http://localhost:8000/healthz

# 2. Check frontend
curl http://localhost:3000

# 3. Test API connection
curl http://localhost:8000/api/auth/me -H "Cookie: jwt=..."

# 4. Test build
cd frontend && npm run build
```

---

**Status:** ✅ Ready for use  
**Build Time:** ~3 hours  
**Version:** 1.0  
**Date:** October 13, 2025

