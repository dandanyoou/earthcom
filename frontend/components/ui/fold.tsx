import type { DetailsHTMLAttributes, ReactNode } from "react";

export function Fold({
  children,
  className = "",
  summary,
  ...props
}: DetailsHTMLAttributes<HTMLDetailsElement> & { summary: ReactNode }) {
  return (
    <details className={`fold ${className}`.trim()} {...props}>
      <summary>{summary}</summary>
      <div className="fold__body">{children}</div>
    </details>
  );
}
