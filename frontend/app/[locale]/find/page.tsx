import { setRequestLocale } from "next-intl/server";

import { NightScreen } from "@/components/feature/world/night-screen";
import { FindScreen } from "@/components/screens/find-screen";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <NightScreen activeTab="find">
      <FindScreen />
    </NightScreen>
  );
}
