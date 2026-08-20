"use client";

// Wraps the globe home and stamps the viewer's local time-of-day onto the
// stage, so the whole screen (and the globe's wash) shifts dark↔light through
// the day — night is deep and cosmic, midday is bright and airy.

import { useEffect, useState } from "react";

import { todFor, type Tod } from "@/lib/city-time";
import styles from "@/app/[locale]/world/world.module.css";

export function WorldStage({ children }: { children: React.ReactNode }) {
  const [tod, setTod] = useState<Tod>("night");

  useEffect(() => {
    const tick = () => setTod(todFor(new Date().getHours()));
    tick();
    const id = setInterval(tick, 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={styles.stage} data-tod={tod}>
      {children}
      <div className={styles.todWash} aria-hidden />
    </div>
  );
}
