import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Deployment Setup - AI Bookkeeper',
  robots: {
    index: false,
    follow: false,
  },
};

export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return children;
}

