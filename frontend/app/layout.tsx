import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import GoogleAnalytics from "@/components/GoogleAnalytics";

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
        <footer className="bg-gray-900 text-white py-8 mt-auto">
          <div className="container mx-auto px-4 max-w-7xl">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="font-bold text-lg mb-4">AI Bookkeeper</h3>
                <p className="text-gray-400 text-sm">
                  Automated bookkeeping powered by AI
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="/pricing" className="text-gray-400 hover:text-white">Pricing</a></li>
                  <li><a href="/gpt-bridge" className="text-gray-400 hover:text-white">ChatGPT Integration</a></li>
                  <li><a href="/tools/csv-cleaner" className="text-gray-400 hover:text-white">CSV Cleaner</a></li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Legal</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="/privacy" className="text-gray-400 hover:text-white">Privacy Policy</a></li>
                  <li><a href="/terms" className="text-gray-400 hover:text-white">Terms of Service</a></li>
                  <li><a href="/dpa" className="text-gray-400 hover:text-white">DPA</a></li>
                  <li><a href="/security" className="text-gray-400 hover:text-white">Security</a></li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Contact</h4>
                <ul className="space-y-2 text-sm">
                  <li><a href="mailto:support@ai-bookkeeper.app" className="text-gray-400 hover:text-white">Support</a></li>
                  <li><a href="mailto:sales@ai-bookkeeper.app" className="text-gray-400 hover:text-white">Sales</a></li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
              © {new Date().getFullYear()} AI Bookkeeper. All rights reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

