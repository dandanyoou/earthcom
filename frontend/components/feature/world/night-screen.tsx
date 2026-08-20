// Wraps the PANGAEA app tabs (찾기·크루·기록) so they share the dark, cosmic
// look of the globe home instead of appearing as disconnected white screens.
// The token overrides live in the CSS module; here we just compose the dark
// stage, the screen content, and the floating glass dock.

import type { ReactNode } from "react";

import type { TabId } from "@/components/shell/tab-bar";
import { WorldDock } from "./world-dock";
import styles from "./night-screen.module.css";

export function NightScreen({ activeTab, children }: { activeTab: TabId; children: ReactNode }) {
  return (
    <div className={styles.stage}>
      <div className={styles.col}>{children}</div>
      <WorldDock activeTab={activeTab} />
    </div>
  );
}
