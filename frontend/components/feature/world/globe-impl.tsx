"use client";

// The Earth(us) globe: a night-earth sphere with the five cities as glowing,
// clickable markers. Clicking a city routes into its scroll-world. Browser-only
// (WebGL + window), so it is always loaded via dynamic(ssr:false).

import Globe, { type GlobeMethods } from "react-globe.gl";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { CITIES, type City, type Locale } from "@/lib/world-cities";
import { todFor, type Tod } from "@/lib/city-time";

const NIGHT_TEX = "https://unpkg.com/three-globe/example/img/earth-night.jpg";
const DAY_TEX = "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg";

export default function GlobeImpl({ locale }: { locale: Locale }) {
  const router = useRouter();
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  // The globe brightens/darkens with the viewer's local time.
  const [tod, setTod] = useState<Tod>("night");
  useEffect(() => {
    const tick = () => setTod(todFor(new Date().getHours()));
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, []);
  const daylit = tod === "day" || tod === "morning";

  useEffect(() => {
    const onResize = () => {
      if (wrapRef.current)
        setSize({ w: wrapRef.current.clientWidth, h: wrapRef.current.clientHeight });
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    const g = globeRef.current;
    if (!g || size.w === 0) return;
    const controls = g.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.55;
    controls.enableZoom = false;
    g.pointOfView({ lat: 32, lng: 90, altitude: 2.4 }, 0);
  }, [size.w]);

  const points = useMemo(() => CITIES.slice(), []);
  const go = (c: City) => router.push(`/${locale}/world/${c.key}`);

  return (
    <div ref={wrapRef} style={{ position: "absolute", inset: 0 }}>
      {size.w > 0 && (
        <Globe
          ref={globeRef}
          width={size.w}
          height={size.h}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl={daylit ? DAY_TEX : NIGHT_TEX}
          atmosphereColor={daylit ? "#bcd8ff" : "#8fb6ff"}
          atmosphereAltitude={daylit ? 0.28 : 0.2}
          pointsData={points}
          pointLat={(d) => (d as City).lat}
          pointLng={(d) => (d as City).lng}
          pointColor={(d) => (d as City).accent}
          pointAltitude={0.07}
          pointRadius={0.6}
          onPointClick={(d) => go(d as City)}
          labelsData={points}
          labelLat={(d) => (d as City).lat}
          labelLng={(d) => (d as City).lng}
          // globe.gl draws labels to a canvas texture whose font lacks Hangul,
          // so Korean rendered as "???". Use the Latin name — always legible.
          labelText={(d) => (d as City).name.en}
          labelColor={(d) => (d as City).accent}
          labelSize={1.6}
          labelDotRadius={0.5}
          labelAltitude={0.07}
          labelResolution={2}
          onLabelClick={(d) => go(d as City)}
        />
      )}
    </div>
  );
}
