"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type DashboardCardProps = {
  title?: string;
  toolbar?: ReactNode;
  children?: ReactNode;
  className?: string;
  contentClassName?: string;
  fill?: boolean;
};

export function DashboardCard({
  title,
  toolbar,
  children,
  className,
  contentClassName,
  fill = false,
}: DashboardCardProps) {
  return (
    <section
      className={cn(
        "relative flex flex-col overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)]",
        fill && "min-h-0 flex-1",
        className,
      )}
    >
      {(title || toolbar) && (
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--color-border)] px-4 py-2.5">
          {title ? (
            <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
          ) : (
            <span />
          )}
          {toolbar}
        </header>
      )}
      <div className={cn("min-h-0 flex-1 p-4", contentClassName)}>{children}</div>
    </section>
  );
}
