import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { NavigationIcon, type NavigationIconName } from "./icons";

export type TabId = "home" | "find" | "signals" | "crew" | "history";

export const tabs: ReadonlyArray<{
  id: TabId;
  href: string;
  icon: NavigationIconName;
}> = [
  { id: "home", href: "/world", icon: "home" },
  { id: "find", href: "/find", icon: "search" },
  { id: "signals", href: "/signals", icon: "signal" },
  { id: "crew", href: "/chat", icon: "crew" },
  { id: "history", href: "/done", icon: "history" },
];

export function TabBar({ activeTab }: { activeTab: TabId }) {
  const t = useTranslations("navigation");

  return (
    <nav className="tab-bar" aria-label={t("ariaLabel")} data-testid="tab-bar">
      {tabs.map((tab) => (
        <Link
          className="tab-bar__link"
          data-active={tab.id === activeTab}
          href={tab.href}
          key={tab.id}
        >
          <span className="tab-bar__icon">
            <NavigationIcon name={tab.icon} />
          </span>
          <span>{t(tab.id)}</span>
        </Link>
      ))}
    </nav>
  );
}
