import { setRequestLocale } from "next-intl/server";

import { NightScreen } from "@/components/feature/world/night-screen";
import { WriteScreen } from "@/components/screens/write-screen";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <NightScreen activeTab="signals">
      <WriteScreen />
    </NightScreen>
  );
}
