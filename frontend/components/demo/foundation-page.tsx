import { useTranslations } from "next-intl";

import { AppShell } from "@/components/shell/app-shell";
import type { TabId } from "@/components/shell/tab-bar";

export function FoundationPage({
  activeTab,
  embedded = false,
}: {
  activeTab: TabId;
  embedded?: boolean;
}) {
  const t = useTranslations("foundation");

  return (
    <AppShell activeTab={activeTab} embedded={embedded}>
      <section className="foundation-page">
        <p className="foundation-page__eyebrow">{t("eyebrow")}</p>
        <h1>{t(`${activeTab}.title`)}</h1>
        <p>{t(`${activeTab}.description`)}</p>
        <div className="foundation-card">
          <strong>{t("cardTitle")}</strong>
          <span>{t("cardStatus")}</span>
        </div>
      </section>
    </AppShell>
  );
}
