# AI Bookkeeper - Next.js Frontend

Modern React frontend built with Next.js 15, NextUI v2 (HeroUI), and Tailwind CSS.

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **UI Library:** NextUI v2 (HeroUI) - Note: Package deprecated, migrating to @heroui/react recommended
- **Styling:** Tailwind CSS
- **Language:** TypeScript
- **Backend:** FastAPI (proxied via Next.js rewrites)

## Features

- 🎨 Responsive dark mode UI with NextUI components
- 📊 Dashboard with metrics cards
- 📋 Transactions table with filtering and multi-select
- 🔄 API proxy to FastAPI backend (localhost:8000)
- ⚡ Server-side rendering with App Router
- 🎭 Brandable theme tokens (primary, success, warning, danger)

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- FastAPI backend running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Dashboard (home)
│   ├── transactions/
│   │   └── page.tsx          # Transactions table
│   ├── layout.tsx            # Root layout
│   ├── providers.tsx         # NextUI provider
│   └── globals.css           # Tailwind imports
├── components/
│   ├── layout/
│   │   └── AppShell.tsx      # Sidebar + topbar shell
│   └── theme-toggle.tsx      # Dark mode switch
├── tailwind.config.ts        # Tailwind + NextUI config
├── next.config.js            # Next.js config (API proxy)
└── tsconfig.json             # TypeScript config
```

## API Integration

The frontend proxies API requests to the FastAPI backend:

- **Frontend:** `http://localhost:3000`
- **Backend:** `http://localhost:8000`
- **Proxy:** `/api/*` → `http://localhost:8000/api/*`

All API calls from the frontend are automatically proxied to the backend via Next.js rewrites.

## Theming

Customize theme colors in `tailwind.config.ts`:

```ts
themes: {
  light: {
    colors: {
      primary: { DEFAULT: "#0ea5e9" },   // sky-500
      success: { DEFAULT: "#16a34a" },   // green-600
      warning: { DEFAULT: "#f59e0b" },   // amber-500
      danger:  { DEFAULT: "#ef4444" }    // red-500
    }
  }
}
```

## Dark Mode

Toggle dark mode via the switch in the top navigation bar. Dark mode is controlled by the `dark` class on the `<html>` element.

## Note: NextUI → HeroUI Migration

NextUI v2 packages are deprecated. For future updates, consider migrating to `@heroui/react`:

```bash
npm uninstall @nextui-org/react @nextui-org/theme
npm install @heroui/react
```

Update imports:
```ts
// Before
import { Button } from "@nextui-org/react";

// After
import { Button } from "@heroui/react";
```

## License

See main project LICENSE.

