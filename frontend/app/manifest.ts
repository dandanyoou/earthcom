import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "PANGAEA",
    short_name: "PANGAEA",
    description: "국경을 넘어 함께 만드는 협업 플랫폼",
    start_url: "/ko/home",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#17223a",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "maskable" },
    ],
  };
}
