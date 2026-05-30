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
    <header className={cn("flex items-end justify-between gap-4 rounded-[12px] border border-[var(--color-border)] bg-white p-5 shadow-[var(--shadow-card)]", className)}>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-[1.25rem] font-semibold tracking-tight text-[var(--color-text)]">{title}</h1>
          {badge ? <div>{badge}</div> : null}
        </div>
        {subtitle ? <div className="mt-2 text-sm text-[var(--color-text-muted)]">{subtitle}</div> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  );
}
