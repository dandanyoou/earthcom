import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { SignalDetailScreen } from "@/components/screens/signal-detail-screen";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="home">
      <SignalDetailScreen signalId={id} />
    </AppShell>
  );
}
