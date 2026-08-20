import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import { NavigationIcon } from "./icons";
import styles from "./shell.module.css";
import { tabs, type TabId } from "./tab-bar";

export function SideNav({ activeTab }: { activeTab: TabId }) {
  const t = useTranslations("navigation");

  return (
    <aside className={styles.sideNav} data-testid="side-nav">
      <Link className={styles.brand} href="/">
        {t("brand")}
      </Link>
      <nav aria-label={t("ariaLabel")} className={styles.sideNavLinks}>
        {tabs.map((tab) => (
          <Link
            className={styles.sideNavLink}
            data-active={tab.id === activeTab}
            href={tab.href}
            key={tab.id}
          >
            <span className={styles.sideNavIcon}>
              <NavigationIcon name={tab.icon} />
            </span>
            <span>{t(tab.id)}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
