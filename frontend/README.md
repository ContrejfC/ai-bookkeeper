# AI Bookkeeper Frontend

Modern Next.js frontend for the AI Bookkeeper application built with NextUI v2 and TypeScript.

## Features

### ✅ Implemented Pages

1. **Authentication**
   - Login page with dev magic link support
   - JWT-based authentication with HttpOnly cookies
   - Protected routes with automatic redirect
   - User context and auth hooks

2. **Dashboard** (`/`)
   - Key metrics overview
   - Recent activity feed
   - Quick stats cards

3. **Transactions** (`/transactions`)
   - Transaction listing with filters
   - Bulk approval workflow
   - Status indicators (proposed, approved, posted)
   - Search and filter capabilities

4. **Receipts** (`/receipts`)
   - Receipt listing with OCR status
   - Individual receipt viewer (`/receipts/[id]`)
   - OCR field extraction with bounding boxes
   - Visual highlighting of extracted fields
   - Confidence scores per field

5. **Rules Console** (`/rules`)
   - Rule candidate management
   - Dry-run simulation (read-only)
   - Accept/reject candidates
   - Version history and rollback
   - Impact analysis

6. **Vendors** (`/vendors`)
   - Vendor listing with automation rates
   - Transaction counts per vendor
   - Rule status indicators
   - Search functionality

7. **Firm Settings** (`/firm`)
   - Tenant listing (RBAC filtered)
   - Settings management (owner only)
   - Auto-post threshold configuration
   - LLM cap management
   - Audit trail for changes

8. **Audit Export** (`/audit`)
   - Filterable CSV export
   - Date range selection
   - Multiple filter criteria
   - Memory-bounded streaming (100k+ rows)

9. **Analytics** (`/analytics`)
   - Automation rate metrics
   - Daily activity trends
   - Top vendors by volume
   - Manual review reasons breakdown
   - System performance metrics

10. **Export** (`/export`)
    - QuickBooks Online integration
    - Xero integration
    - Idempotent exports
    - Export history and status

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **UI Library:** NextUI v2
- **Styling:** Tailwind CSS
- **Language:** TypeScript
- **State Management:** React Context (Auth)
- **HTTP Client:** Fetch API with custom wrapper

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn
- Backend API running (see main README)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with your API URL
```

### Development

```bash
# Run development server
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── login/             # Authentication
│   ├── transactions/      # Transaction management
│   ├── receipts/          # Receipt OCR
│   │   └── [id]/         # Individual receipt viewer
│   ├── rules/             # Rules console
│   ├── vendors/           # Vendor management
│   ├── firm/              # Firm/tenant settings
│   ├── audit/             # Audit export
│   ├── analytics/         # Analytics dashboard
│   ├── export/            # QBO/Xero export
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard
│   ├── providers.tsx      # Client-side providers
│   └── globals.css        # Global styles
├── components/
│   ├── layout/
│   │   └── AppShell.tsx   # Main app layout
│   ├── protected-route.tsx # Route guard
│   └── theme-toggle.tsx   # Dark/light mode toggle
├── contexts/
│   └── auth-context.tsx   # Auth state management
├── lib/
│   └── api.ts             # API client and helpers
└── public/                # Static assets
```

## API Integration

The frontend communicates with the backend API through a centralized API client (`lib/api.ts`). All requests include credentials for cookie-based JWT authentication.

### API Modules

- `authAPI` - Authentication endpoints
- `tenantsAPI` - Tenant management
- `rulesAPI` - Rules console
- `auditAPI` - Audit export
- `transactionsAPI` - Transaction management
- `exportAPI` - QBO/Xero integration

## Authentication Flow

1. User logs in via `/login`
2. Backend sets HttpOnly cookie with JWT
3. Auth context fetches user info on mount
4. Protected routes check auth status
5. Automatic redirect to login if unauthenticated

### Dev Mode

In development, a magic link button is available for quick testing:
- Email: `admin@example.com`
- Magic token: `dev`

## Theming

The app supports dark mode by default with NextUI's theming system. Users can toggle between light and dark modes using the theme switcher in the navbar.

## RBAC (Role-Based Access Control)

The frontend respects user roles from the backend:

- **Owner:** Full access to all tenants and settings
- **Staff:** Limited to assigned tenants, read-only on settings

Role checks are performed in components and enforced by the backend API.

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API base URL (required)

## Performance

- Server components where possible
- Client components only when interactivity needed
- Optimized bundle size with tree shaking
- Fast page transitions with Next.js routing

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

See main project README for contribution guidelines.

## License

See main project LICENSE file.
