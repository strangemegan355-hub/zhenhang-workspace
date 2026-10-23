/** Shared form & panel classes — aligned with dashboard / globals.css tokens */

export const fieldInputClass =
  "h-10 w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-soft)] focus:border-[var(--color-primary)] focus:outline-none";

export const fieldTextareaClass =
  "min-h-[80px] w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-soft)] focus:border-[var(--color-primary)] focus:outline-none";

export const searchInputClass =
  "h-10 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-soft)] focus:border-[var(--color-primary)] focus:outline-none";

export const fieldLabelClass = "text-sm text-[var(--color-text-muted)]";

export const kpiCardClass =
  "rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3";

export const kpiCardLabelClass = "text-sm text-[var(--color-text-muted)]";

export const kpiCardValueClass = "mt-1 text-lg font-medium tabular-nums text-[var(--color-text)]";

export const tableHeaderRowClass = "border-b border-[var(--color-border)] text-sm text-[var(--color-text-muted)]";

export const tableBodyRowClass = "border-b border-[var(--color-border-soft)] text-sm";

/** Money cells: right-aligned tabular nums (UI_DESIGN_SYSTEM §5) */
export const moneyCellClass = "px-2 py-2 text-right tabular-nums";

/** FilterBar field: consistent min width + label stack (PAGE_LAYOUT_STANDARD §1) */
export const filterFieldClass = "block min-w-[160px] space-y-1 text-xs";

/** FilterBar checkbox aligned to control row height */
export const filterCheckClass =
  "flex h-10 items-center gap-2 text-xs text-[var(--color-text-muted)]";

export const formPanelClass =
  "rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface-soft)] p-4";

export const messageBannerClass =
  "rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2 text-sm text-[var(--color-text)]";

export const rowHoverClass = "hover:bg-[var(--color-surface-soft)]";

export const linkActionClass = "text-sm text-[var(--color-primary)] hover:underline";

export const dangerActionClass = "text-sm text-[var(--color-danger)] hover:underline";

export const inlineBtnClass =
  "rounded border border-[var(--color-border)] px-2.5 py-1 text-sm text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-soft)]";

export const inlineBtnDangerClass =
  "rounded border border-[var(--color-accent-soft)] px-2.5 py-1 text-sm text-[var(--color-danger)] transition-colors hover:bg-[var(--color-accent-soft)]";

export const sectionDividerClass = "border-t border-[var(--color-border)] pt-4";
