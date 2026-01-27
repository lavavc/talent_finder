/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/talent_finder',
  assetPrefix: '/talent_finder',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

module.exports = nextConfig;
