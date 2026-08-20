/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  experimental: {
    allowedDevOrigins: [
      'localhost:22313',
      '127.0.0.1:22313',
      '192.168.1.230:22313',
    ],
  },
};

module.exports = nextConfig;
