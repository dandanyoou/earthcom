import type { SVGProps } from "react";

export type NavigationIconName = "home" | "search" | "crew" | "history";

export function NavigationIcon({
  name,
  ...props
}: SVGProps<SVGSVGElement> & { name: NavigationIconName }) {
  if (name === "home") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
        <path d="M3 10.5 12 3l9 7.5" />
        <path d="M5.5 9.5V20h13V9.5" />
      </svg>
    );
  }

  if (name === "search") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m15.5 15.5 4.5 4.5" />
      </svg>
    );
  }

  if (name === "crew") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
        <circle cx="8.5" cy="8" r="3.2" />
        <circle cx="16.5" cy="9.5" r="2.6" />
        <path d="M3 19c0-3 2.5-4.8 5.5-4.8S14 16 14 19" />
        <path d="M15.5 14.4c2.7.2 4.5 1.9 4.5 4.6" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 1.8" />
    </svg>
  );
}
