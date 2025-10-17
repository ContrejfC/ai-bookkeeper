/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Output standalone for Docker deployment
  output: 'standalone',
  async rewrites() {
    // Proxy to separate API service
    // Use NEXT_PUBLIC_API_URL env var (set in Render)
    // Default to localhost for local development
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/healthz',
        destination: `${apiUrl}/healthz`,
      },
      {
        source: '/readyz',
        destination: `${apiUrl}/readyz`,
      },
      {
        source: '/actions',
        destination: `${apiUrl}/actions`,
      },
      {
        source: '/openapi.json',
        destination: `${apiUrl}/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;

