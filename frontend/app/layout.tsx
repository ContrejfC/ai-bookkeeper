import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import GoogleAnalytics from "@/components/GoogleAnalytics";
import { BuildTag } from "@/components/BuildTag";

export const metadata: Metadata = {
  title: "AI Bookkeeper - Automated Bookkeeping with AI",
  description: "Calibrated, explainable bookkeeping automation with AI-powered transaction categorization, journal entries, and QuickBooks/Xero integration."
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: '#10b981'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const gaId = process.env.NEXT_PUBLIC_GA_ID || '';
  
  return (
    <html lang="en" className="dark">
      <head>
        <GoogleAnalytics gaId={gaId} />
      </head>
      <body>
        <Providers>{children}</Providers>
        <BuildTag />
      </body>
    </html>
  );
}

