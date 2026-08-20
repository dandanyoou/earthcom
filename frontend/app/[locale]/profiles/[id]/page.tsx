import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { ProfileScreen } from "@/components/screens/profile-screen";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="find">
      <ProfileScreen profileId={id} />
    </AppShell>
  );
}
