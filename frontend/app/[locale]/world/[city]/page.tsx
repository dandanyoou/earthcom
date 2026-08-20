import { existsSync } from "node:fs";
import { join } from "node:path";

import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";

import { CITIES, findCity, type Locale } from "@/lib/world-cities";
import { CityVillage } from "@/components/feature/world/city-world";
import { WorldDock } from "@/components/feature/world/world-dock";

export function generateStaticParams() {
  return CITIES.flatMap((c) => ["ko", "en"].map((locale) => ({ locale, city: c.key })));
}

// Only reference connector clips that actually exist on disk. A missing one is
// passed as null so the engine crossfades that seam instead of 404-ing — the
// village stills always show regardless.
function connectorsFor(cityKey: string): (string | null)[] {
  const dir = join(process.cwd(), "public", "scroll-world", cityKey);
  return [1, 2, 3, 4].map((n) =>
    existsSync(join(dir, `conn${n}.mp4`)) ? `/scroll-world/${cityKey}/conn${n}.mp4` : null,
  );
}

export default async function CityWorldPage({
  params,
}: {
  params: Promise<{ locale: string; city: string }>;
}) {
  const { locale, city } = await params;
  setRequestLocale(locale);
  const found = findCity(city);
  if (!found) notFound();
  const loc: Locale = locale === "en" ? "en" : "ko";
  return (
    <>
      <CityVillage city={found} locale={loc} connectors={connectorsFor(found.key)} />
      <WorldDock activeTab="home" />
    </>
  );
}
