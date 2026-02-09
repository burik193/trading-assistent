/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // In dev, proxy /api to backend so same-origin requests work (no CORS, no NEXT_PUBLIC_API_URL needed)
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    const backend = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};
module.exports = nextConfig;
