/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output standalone for Docker deployment
  output: 'standalone',
  
  // API rewrites - proxy /api requests to FastAPI backend
  async rewrites() {
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
    ];
  },
};

export default nextConfig;

