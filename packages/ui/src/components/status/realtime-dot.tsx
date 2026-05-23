"use client";

import { legacyLevelToStatus, statusPalette, type InteractionStatus } from "../../theme/interaction-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";

export type RealtimeDotLevel = "ok" | "warn" | "error" | "idle";

export type RealtimeDotProps = {
  level: RealtimeDotLevel;
  label: string;
  pulse?: boolean;
  status?: InteractionStatus;
  className?: string;
};

export function RealtimeDot({ level, label, pulse, status, className }: RealtimeDotProps) {
  const resolved = status ?? legacyLevelToStatus(level);
  const palette = statusPalette(resolved);
  const shouldPulse = pulse ?? resolved === "processing";

  return (
    <span className={cn("inline-flex items-center gap-1.5", typography.caption, className)}>
      <span className="relative flex h-2 w-2 shrink-0">
        {shouldPulse ? (
          <span
            className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-40"
            style={{ backgroundColor: palette.fg }}
          />
        ) : null}
        <span
          className="relative inline-flex h-2 w-2 rounded-full"
          style={{ backgroundColor: palette.fg }}
        />
      </span>
      <span style={{ color: palette.fg }}>{label}</span>
    </span>
  );
}
