import type { ReactNode } from "react";

import { DesktopShell } from "./desktop-shell";
import { MobileShell } from "./mobile-shell";
import type { TabId } from "./tab-bar";

export function AppShell({
  activeTab,
  children,
  embedded = false,
}: {
  activeTab: TabId;
  children: ReactNode;
  embedded?: boolean;
}) {
  if (embedded) {
    return (
      <MobileShell activeTab={activeTab} embedded>
        {children}
      </MobileShell>
    );
  }

  return <DesktopShell activeTab={activeTab}>{children}</DesktopShell>;
}
