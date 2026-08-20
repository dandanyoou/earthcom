import Link from "next/link";
import { setRequestLocale } from "next-intl/server";

import { CITIES, type Locale } from "@/lib/world-cities";
import { PangaeaGlobe } from "@/components/feature/world/pangaea-globe";
import { HomeWidgets } from "@/components/feature/world/home-widgets";
import { WorldStage } from "@/components/feature/world/world-stage";
import { WorldDock } from "@/components/feature/world/world-dock";
import styles from "./world.module.css";

export default async function WorldHome({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const loc: Locale = locale === "en" ? "en" : "ko";

  return (
    <WorldStage>
      <PangaeaGlobe locale={loc} />

      <div className={styles.hud}>
        <header className={styles.hero}>
          <p className={styles.eyebrow}>PANGAEA</p>
          <h1 className={styles.title}>
            {loc === "ko" ? "국경 없는 하나의 세계" : "One world, no borders"}
          </h1>
          <p className={styles.sub}>
            {loc === "ko"
              ? "지구본에서 도시를 골라, 그 도시의 이야기 속으로 들어가세요."
              : "Pick a city on the globe and step into its story."}
          </p>
          <HomeWidgets locale={loc} />
        </header>

        <nav className={styles.rail} aria-label={loc === "ko" ? "도시 목록" : "Cities"}>
          {CITIES.map((c) => (
            <Link
              key={c.key}
              href={`/${locale}/world/${c.key}`}
              className={styles.chip}
              style={{ ["--accent" as string]: c.accent }}
            >
              <span className={styles.chipName}>{c.name[loc]}</span>
              <span className={styles.chipRole}>{c.role[loc]}</span>
            </Link>
          ))}
        </nav>
      </div>

      <WorldDock activeTab="home" />
    </WorldStage>
  );
}
