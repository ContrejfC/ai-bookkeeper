/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Output standalone for Docker deployment
  output: 'standalone',
  async rewrites() {
    // In production (Docker), proxy to backend on localhost:8000
    // In development, proxy to local backend
    const apiUrl = process.env.NODE_ENV === 'production' 
      ? 'http://localhost:8000'
      : 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      // Health checks (Render hits frontend port 10000)
      {
        source: '/healthz',
        destination: `${apiUrl}/healthz`,
      },
      {
        source: '/readyz',
        destination: `${apiUrl}/readyz`,
      },
    ];
  },
};

module.exports = nextConfig;

