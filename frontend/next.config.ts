import type { NextConfig } from 'next';

const isStaticExport = process.env.STATIC_EXPORT === 'true';
const pagesBasePath = process.env.GITHUB_PAGES_BASE_PATH ?? '';

const nextConfig: NextConfig = isStaticExport
  ? {
      output: 'export',
      trailingSlash: true,
      basePath: pagesBasePath,
      assetPrefix: pagesBasePath,
      images: { unoptimized: true },
    }
  : {};

export default nextConfig;
