"use client";

import dynamic from "next/dynamic";
import type { Locale } from "@/lib/world-cities";

// WebGL globe: browser-only.
const GlobeImpl = dynamic(() => import("./globe-impl"), {
  ssr: false,
  loading: () => (
    <div style={{ position: "absolute", inset: 0, background: "#05070f" }} aria-hidden="true" />
  ),
});

export function PangaeaGlobe({ locale }: { locale: Locale }) {
  return <GlobeImpl locale={locale} />;
}
