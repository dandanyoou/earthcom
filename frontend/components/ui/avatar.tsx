import type { HTMLAttributes } from "react";

export type AvatarPalette = 1 | 2 | 3 | 4 | 5 | 6;

export function Avatar({
  className = "",
  palette = 1,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { palette?: AvatarPalette }) {
  return (
    <span
      aria-hidden="true"
      className={`avatar ${className}`.trim()}
      data-palette={palette}
      {...props}
    />
  );
}
