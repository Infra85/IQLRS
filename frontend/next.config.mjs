import {fileURLToPath} from "node:url";
/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: fileURLToPath(new URL(".", import.meta.url)),
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  async rewrites() {
    const backend = process.env.API_PROXY_URL || "http://127.0.0.1:8000";
    return [{source: "/api/:path*", destination: `${backend}/api/:path*`}];
  },
  async headers() {
    return [{source: "/:path*", headers: [
      {key: "X-Content-Type-Options", value: "nosniff"},
      {key: "X-Frame-Options", value: "DENY"},
      {key: "Referrer-Policy", value: "strict-origin-when-cross-origin"},
    ]}];
  },
};
export default nextConfig;
