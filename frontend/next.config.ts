import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: "/qa",
        destination: "http://127.0.0.1:8001/qa",
      },
      {
        source: "/index-pdf",
        destination: "http://127.0.0.1:8001/index-pdf",
      },
    ];
  },
};

export default nextConfig;
