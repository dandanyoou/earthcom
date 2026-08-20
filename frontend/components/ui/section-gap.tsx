import type { HTMLAttributes } from "react";

export function SectionGap({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div aria-hidden="true" className={`section-gap ${className}`.trim()} {...props} />;
}
