"use client";

// A glassy floating dock for the globe/village world. The app's default
// .tab-bar is a solid white bar that reads as a foreign panel over the dark
// globe; this one is translucent and rounded so it sits ON the world rather
// than under it. Same destinations as the app navigation.

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import { NavigationIcon } from "@/components/shell/icons";
import { tabs, type TabId } from "@/components/shell/tab-bar";
import styles from "./world-dock.module.css";

export function WorldDock({ activeTab }: { activeTab: TabId }) {
  const t = useTranslations("navigation");

  return (
    <nav className={styles.dock} aria-label={t("ariaLabel")} data-testid="world-dock">
      {tabs.map((tab) => (
        <Link
          key={tab.id}
          href={tab.href}
          className={styles.link}
          data-active={tab.id === activeTab}
        >
          <span className={styles.icon}>
            <NavigationIcon name={tab.icon} />
          </span>
          <span className={styles.label}>{t(tab.id)}</span>
        </Link>
      ))}
    </nav>
  );
}
