"use client";

import type { CSSProperties, ReactNode } from "react";
import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";
import { InlineLoadingBar } from "../loading/inline-loading-bar";
import { PanelSkeleton } from "../loading/panel-skeleton";
import { EmptyState } from "../loading/empty-state";

export type IndustrialPanelProps = {
  title?: string;
  toolbar?: ReactNode;
  children?: ReactNode;
  className?: string;
  contentClassName?: string;
  loading?: boolean;
  inlineLoading?: boolean;
  empty?: boolean;
  emptyMessage?: string;
  headerExtra?: ReactNode;
  /** Expand panel to fill available workspace height */
  fill?: boolean;
};

export function IndustrialPanel({
  title,
  toolbar,
  children,
  className,
  contentClassName,
  loading = false,
  inlineLoading = false,
  empty = false,
  emptyMessage = "暂无数据",
  headerExtra,
  fill = false,
}: IndustrialPanelProps) {
  const shellStyle: CSSProperties = {
    backgroundColor: designTokens.colors.background.panel,
    border: `1px solid ${designTokens.colors.border.default}`,
    borderRadius: designTokens.radius.sm,
    boxShadow: designTokens.shadow.sm,
  };

  const hasHeader = Boolean(title || toolbar || headerExtra);
  const pad = interactionTokens.layout.panelPadding;

  return (
    <section
      className={cn("relative flex flex-col overflow-hidden", fill && "min-h-0 flex-1", className)}
      style={shellStyle}
    >
      <InlineLoadingBar active={inlineLoading || loading} />
      {hasHeader ? (
        <header
          className="flex shrink-0 flex-col gap-2 border-b"
          style={{
            borderColor: designTokens.colors.border.muted,
            padding: `${pad}px ${pad}px 8px`,
            minHeight: interactionTokens.layout.toolbar,
          }}
        >
          {title || headerExtra ? (
            <div className="flex min-w-0 items-center justify-between gap-2">
              <div className="min-w-0">
                {title ? <h2 className={typography.cardTitle}>{title}</h2> : null}
              </div>
              {headerExtra ? <div className="flex shrink-0 items-center gap-2">{headerExtra}</div> : null}
            </div>
          ) : null}
          {toolbar ? <div className="flex flex-wrap items-center gap-2">{toolbar}</div> : null}
        </header>
      ) : null}

      <div className={cn("flex min-h-0 flex-1 flex-col", contentClassName)} style={{ padding: pad }}>
        {loading ? (
          <PanelSkeleton />
        ) : empty ? (
          <EmptyState message={emptyMessage} />
        ) : (
          children
        )}
      </div>
    </section>
  );
}
