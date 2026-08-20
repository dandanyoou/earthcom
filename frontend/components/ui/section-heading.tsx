import type { HTMLAttributes, ReactNode } from "react";

export function SectionHeading({
  children,
  className = "",
  count,
  ...props
}: HTMLAttributes<HTMLHeadingElement> & { count?: ReactNode }) {
  return (
    <h2 className={`section-heading ${className}`.trim()} {...props}>
      {children}
      {count === undefined ? null : <small>{count}</small>}
    </h2>
  );
}
