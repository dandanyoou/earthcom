import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { ApplicationsScreen } from "@/components/screens/applications-screen";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="crew">
      <ApplicationsScreen />
    </AppShell>
  );
}
