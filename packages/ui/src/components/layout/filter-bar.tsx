import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

/** Standard list-page filter row (PAGE_LAYOUT_STANDARD §1 FilterBar). */
export function FilterBar({
  children,
  className,
  "aria-label": ariaLabel = "筛选",
}: {
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
}) {
  return (
    <div
      role="search"
      aria-label={ariaLabel}
      className={cn("mb-3 flex flex-wrap items-end gap-3", className)}
    >
      {children}
    </div>
  );
}
