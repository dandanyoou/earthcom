import type { ReactNode } from "react";

import { TabBar, type TabId } from "./tab-bar";

export function MobileShell({
  activeTab,
  children,
  embedded = false,
}: {
  activeTab: TabId;
  children: ReactNode;
  embedded?: boolean;
}) {
  return (
    <div className="mobile-shell" data-embedded={embedded}>
      <main className="mobile-shell__content">{children}</main>
      <TabBar activeTab={activeTab} />
    </div>
  );
}
