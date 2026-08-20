// Per-country local time → time-of-day, used to tint the village diorama and
// show the city's current clock. Offsets are the current (Aug/DST) UTC offsets
// for each city. Compute on the client only (uses the real clock) to avoid an
// SSR hydration mismatch.

import type { CityKey } from "./world-cities";

export const UTC_OFFSET: Record<CityKey, number> = {
  seoul: 9,
  berlin: 2, // CEST
  tokyo: 9,
  lisbon: 1, // WEST
  newyork: -4, // EDT
};

export type Tod = "morning" | "day" | "evening" | "night";

export function localHour(city: CityKey, now: Date): number {
  const utc = now.getUTCHours() + now.getUTCMinutes() / 60;
  return (utc + UTC_OFFSET[city] + 24) % 24;
}

export function todFor(hour: number): Tod {
  if (hour < 6) return "night";
  if (hour < 11) return "morning";
  if (hour < 17) return "day";
  if (hour < 20) return "evening";
  return "night";
}

export function todLabel(tod: Tod, locale: "ko" | "en"): string {
  const map: Record<Tod, Record<"ko" | "en", string>> = {
    morning: { ko: "아침", en: "Morning" },
    day: { ko: "낮", en: "Day" },
    evening: { ko: "저녁", en: "Evening" },
    night: { ko: "밤", en: "Night" },
  };
  return map[tod][locale];
}

export function clockString(city: CityKey, now: Date): string {
  const h = localHour(city, now);
  const hh = Math.floor(h);
  const mm = Math.floor((h - hh) * 60);
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}
