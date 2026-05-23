"use client";

import type { CSSProperties, ReactNode } from "react";
import { statusPalette, type InteractionStatus } from "../../theme/interaction-tokens";
import { cn } from "../../utils/cn";

export type SystemPillProps = {
  status?: InteractionStatus;
  children: ReactNode;
  mono?: boolean;
  className?: string;
};

export function SystemPill({ status = "idle", children, mono = false, className }: SystemPillProps) {
  const palette = statusPalette(status);
  const style: CSSProperties = {
    color: palette.fg,
    backgroundColor: palette.bg,
    border: `1px solid ${palette.border}`,
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 text-[11px] font-medium",
        mono && "font-mono tabular-nums",
        className,
      )}
      style={style}
    >
      {children}
    </span>
  );
}
