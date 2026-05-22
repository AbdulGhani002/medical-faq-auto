/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // ``standalone`` produces a self-contained build under .next/standalone
  // that the Docker image can run with ``node server.js`` instead of
  // ``next start`` — much smaller image, no dev dependencies needed at
  // runtime.
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;
