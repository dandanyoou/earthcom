import type { ReactNode } from "react";

import { SideNav } from "./side-nav";
import styles from "./shell.module.css";
import { TabBar, type TabId } from "./tab-bar";

export function DesktopShell({ activeTab, children }: { activeTab: TabId; children: ReactNode }) {
  return (
    <div className={styles.shell} data-testid="app-shell">
      <SideNav activeTab={activeTab} />
      <div className={styles.viewport}>
        <main className={styles.main} data-testid="shell-main">
          <div className={styles.content} data-testid="shell-content">
            {children}
          </div>
        </main>
        <TabBar activeTab={activeTab} />
      </div>
    </div>
  );
}
