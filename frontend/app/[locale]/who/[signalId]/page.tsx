import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { WhoScreen } from "@/components/screens/who-screen";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; signalId: string }>;
}) {
  const { locale, signalId } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="home">
      <WhoScreen signalId={signalId} />
    </AppShell>
  );
}
