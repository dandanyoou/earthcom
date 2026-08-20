import { setRequestLocale } from "next-intl/server";

import { AppShell } from "@/components/shell/app-shell";
import { WriteScreen } from "@/components/screens/write-screen";

export default async function EditSignalPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  return (
    <AppShell activeTab="signals">
      <WriteScreen signalId={id} />
    </AppShell>
  );
}
