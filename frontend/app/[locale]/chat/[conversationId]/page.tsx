import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { ChatScreen } from "@/components/screens/chat-screens";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; conversationId: string }>;
}) {
  const { locale, conversationId } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="crew">
      <ChatScreen conversationId={conversationId} />
    </AppShell>
  );
}
