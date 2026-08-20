import type { HTMLAttributes, ReactNode } from "react";

function NoteIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3.5 21 20H3Z" />
      <path d="M12 9v5" />
      <path d="M12 17.2v.2" />
    </svg>
  );
}

export function Note({
  children,
  className = "",
  title,
  tone = "warning",
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  title: ReactNode;
  tone?: "warning" | "information";
}) {
  return (
    <div className={`note note--${tone} ${className}`.trim()} {...props}>
      <span className="note__icon">
        <NoteIcon />
      </span>
      <span className="note__body">
        <strong>{title}</strong>
        <span>{children}</span>
      </span>
    </div>
  );
}
