import type { HTMLAttributes } from "react";

export type ChipTone = "verified" | "ai" | "warning" | "danger" | "neutral" | "outline";

export function Chip({
  className = "",
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: ChipTone }) {
  return <span className={`chip chip--${tone} ${className}`.trim()} data-tone={tone} {...props} />;
}
