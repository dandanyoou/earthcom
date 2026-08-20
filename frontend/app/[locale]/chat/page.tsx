import { setRequestLocale } from "next-intl/server";

import { NightScreen } from "@/components/feature/world/night-screen";
import { ChatListScreen } from "@/components/screens/chat-screens";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <NightScreen activeTab="crew">
      <ChatListScreen />
    </NightScreen>
  );
}
