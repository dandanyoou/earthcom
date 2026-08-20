import type { HTMLAttributes } from "react";

export function Row({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`row ${className}`.trim()} {...props} />;
}
