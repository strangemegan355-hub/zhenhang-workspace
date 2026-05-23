"use client";

import type { CSSProperties, ReactNode } from "react";
import {
  interactionTokens,
  statusPalette,
  type InteractionStatus,
} from "../../theme/interaction-tokens";
import { cn } from "../../utils/cn";

export type StatusBadgeProps = {
  status: InteractionStatus;
  label: ReactNode;
  compact?: boolean;
  pulse?: boolean;
  className?: string;
};

export function StatusBadge({ status, label, compact = false, pulse = false, className }: StatusBadgeProps) {
  const palette = statusPalette(status);
  const style: CSSProperties = {
    color: palette.fg,
    backgroundColor: palette.bg,
    border: `1px solid ${palette.border}`,
    fontSize: compact ? 10 : 11,
    padding: compact ? "2px 6px" : "3px 8px",
    lineHeight: 1.2,
    transition: `border-color ${interactionTokens.transition.fast}, background-color ${interactionTokens.transition.fast}`,
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded font-semibold uppercase tracking-wide",
        pulse && "animate-pulse",
        className,
      )}
      style={style}
    >
      {pulse ? (
        <span
          className="h-1.5 w-1.5 shrink-0 rounded-full"
          style={{ backgroundColor: palette.fg }}
        />
      ) : null}
      {label}
    </span>
  );
}
