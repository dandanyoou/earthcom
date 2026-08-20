"use client";

import { useLocale } from "next-intl";

/** Phone-frame showcase (§4.7-6) — the bezel exists only on this page. */
export function DemoSurface() {
  const locale = useLocale();
  return (
    <div className="demo-stage">
      <div className="demo-phone" data-testid="demo-phone">
        <div className="demo-phone__screen">
          <iframe
            src={`/${locale}/home`}
            style={{ border: 0, height: "100%", width: "100%" }}
            title="Earth(us)"
          />
        </div>
      </div>
    </div>
  );
}
