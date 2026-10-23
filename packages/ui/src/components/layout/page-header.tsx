import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

export function PageHeader({
  title,
  subtitle,
  badge,
  actions,
  className,
}: {
  title: string;
  subtitle?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "mb-4 flex items-start justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3",
        className,
      )}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold leading-tight text-[var(--color-text)]">{title}</h1>
          {badge ? <div>{badge}</div> : null}
        </div>
        {subtitle ? <div className="mt-1 text-xs text-[var(--color-text-muted)]">{subtitle}</div> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
