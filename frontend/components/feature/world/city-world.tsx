"use client";

// A country's world, rendered by the scroll-world engine: the visitor SCROLLS
// and the camera dives INTO each category village (a real neighbourhood
// diorama), pulls out, flies over the map, and dives into the next — one
// connected world, no cuts. Five villages per country: 모임·구인구직·섭외·
// 교육교류·연결. Each village's "글 보기" button opens that neighbourhood's
// posts (same .post cards as /ko/home). Nothing auto-plays — scroll is time.

import { useEffect, useMemo, useRef, useState } from "react";

import { Chip } from "@/components/ui";
import type { City, Locale } from "@/lib/world-cities";
import { CATEGORIES, NEIGHBORHOODS, postsFor, type CategoryKey } from "@/lib/village-content";
import { clockString, localHour, todFor, todLabel, type Tod } from "@/lib/city-time";
import styles from "./city-world.module.css";

declare global {
  interface Window {
    mountScrollWorld?: (el: HTMLElement, config: unknown) => void;
  }
}

const ACCENT: Record<CategoryKey, string> = {
  meet: "#7aa2ff",
  work: "#8fe0b0",
  cast: "#ffc978",
  learn: "#6be675",
  connect: "#c9a2ff",
};

const BODY: Record<CategoryKey, Record<Locale, string>> = {
  meet: { ko: "취향으로 모이는 사람들", en: "People who gather by what they love" },
  work: { ko: "필요한 손과 기회가 만나는 곳", en: "Where hands and opportunities meet" },
  cast: { ko: "무대에 설 사람을 찾는 거리", en: "The street that finds who takes the stage" },
  learn: { ko: "가르치고 배우고 나누는 자리", en: "A place to teach, learn and exchange" },
  connect: { ko: "국경 없이 이어지는 사람들", en: "People connected across borders" },
};

const ENGINE_SRC = "/scroll-world/scrub-engine.js";

function loadEngine(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined") return reject();
    if (window.mountScrollWorld) return resolve();
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${ENGINE_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(), { once: true });
      return;
    }
    const s = document.createElement("script");
    s.src = ENGINE_SRC;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject();
    document.head.appendChild(s);
  });
}

export function CityVillage({
  city,
  locale,
  connectors,
}: {
  city: City;
  locale: Locale;
  // One entry per seam (length 4). A null means that connector clip isn't
  // available, so the two villages simply crossfade — the village stills still
  // always show. Computed server-side from what's actually on disk.
  connectors: (string | null)[];
}) {
  const posts = useMemo(() => postsFor(city.key), [city.key]);
  const stageRef = useRef<HTMLDivElement>(null);
  const [sheet, setSheet] = useState<CategoryKey | null>(null);
  const [clock, setClock] = useState("");
  const [tod, setTod] = useState<Tod>("night");

  const hood = (c: CategoryKey) => NEIGHBORHOODS[city.key][c][locale];
  const cat = (key: CategoryKey) => CATEGORIES.find((c) => c.key === key);
  const cityName = city.name[locale];

  // local clock / time-of-day tint
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setClock(clockString(city.key, now));
      setTod(todFor(localHour(city.key, now)));
    };
    tick();
    const id = setInterval(tick, 30_000);
    return () => clearInterval(id);
  }, [city.key]);

  // mount the scroll-world engine once
  useEffect(() => {
    const host = stageRef.current;
    if (!host) return;
    const base = `/scroll-world/${city.key}`;
    const config = {
      brand: { name: cityName, href: `/${locale}/world` },
      hint: locale === "ko" ? "스크롤해서 마을 속으로 ↓" : "scroll into the villages ↓",
      nav: true,
      atmosphere: false, // no drifting bubbles
      connScroll: 0.85,
      diveScroll: 1.35,
      sections: CATEGORIES.map((c) => ({
        id: c.key,
        label: c.label[locale],
        still: `${base}/poster_${c.key}.jpg`,
        clip: `${base}/dive_${c.key}.mp4`,
        accent: ACCENT[c.key],
        eyebrow: `${cityName} · ${hood(c.key)}`,
        title: c.label[locale],
        body: BODY[c.key][locale],
        linger: 0.55,
        cta: {
          primary: {
            label: locale === "ko" ? "글 보기 →" : "See posts →",
            href: `#posts-${c.key}`,
          },
        },
      })),
      connectors,
    };

    let cancelled = false;
    loadEngine()
      .then(() => {
        if (cancelled || !window.mountScrollWorld) return;
        window.mountScrollWorld(host, config);
      })
      .catch(() => {});

    // CTA "글 보기" → open that village's posts. The engine stacks all five
    // copies at one spot, so trust the on-screen (most-opaque) village rather
    // than which stacked anchor got the click.
    const onClick = (e: MouseEvent) => {
      const a = (e.target as HTMLElement)?.closest?.('a[href^="#posts-"]');
      if (!a) return;
      e.preventDefault();
      const copies = Array.from(host.querySelectorAll<HTMLElement>(".sw-copy"));
      let best = -1;
      let bestOp = -1;
      copies.forEach((c, i) => {
        const o = parseFloat(getComputedStyle(c).opacity) || 0;
        if (o > bestOp) {
          bestOp = o;
          best = i;
        }
      });
      const key =
        best >= 0
          ? CATEGORIES[best].key
          : (a.getAttribute("href")!.replace("#posts-", "") as CategoryKey);
      setSheet(key);
    };
    host.addEventListener("click", onClick);
    return () => {
      cancelled = true;
      host.removeEventListener("click", onClick);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city.key, locale]);

  useEffect(() => {
    document.body.style.overflow = sheet ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sheet]);

  const sheetPosts = sheet ? posts.filter((p) => p.cat === sheet) : [];

  return (
    <div className={styles.world} data-tod={tod}>
      {/* engine mounts its diorama flight here */}
      <div ref={stageRef} className={styles.stageHost} />

      {/* time-of-day wash + clock (over the flight, non-interactive) */}
      <div className={styles.tint} aria-hidden />
      <p className={styles.clock}>
        <span className={styles.clockDot} /> {cityName} · {clock} · {todLabel(tod, locale)}
      </p>

      {sheet ? (
        <div className={styles.sheetWrap} role="dialog" aria-modal="true">
          <button
            className={styles.sheetScrim}
            aria-label={locale === "ko" ? "닫기" : "Close"}
            onClick={() => setSheet(null)}
          />
          <div className={styles.sheet}>
            <div className={styles.sheetHead}>
              <div>
                <span className={styles.sheetEyebrow}>
                  {cityName} · {hood(sheet)}
                </span>
                <h2 className={styles.sheetTitle}>{cat(sheet)?.label[locale]}</h2>
              </div>
              <button className={styles.sheetClose} type="button" onClick={() => setSheet(null)}>
                ✕
              </button>
            </div>
            <div className={styles.sheetPosts}>
              {sheetPosts.map((p) => (
                <div key={p.id} className="post">
                  <div className="post__top">
                    <Chip tone={cat(p.cat)?.tone ?? "neutral"}>{cat(p.cat)?.label[locale]}</Chip>
                    <Chip tone="neutral">
                      {p.online
                        ? locale === "ko"
                          ? "온라인"
                          : "Online"
                        : locale === "ko"
                          ? "오프라인"
                          : "On-site"}
                    </Chip>
                    <span className="post__when">{p.when[locale]}</span>
                  </div>
                  <div className="post__title">{p.title[locale]}</div>
                  <div className="post__meta">{p.meta[locale]}</div>
                  {p.faces.length > 0 ? (
                    <div className="faces">
                      {p.faces.map((f, idx) => (
                        <span key={idx} data-palette={f.palette}>
                          {f.initials}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
