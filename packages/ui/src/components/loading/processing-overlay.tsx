"use client";

import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { typography } from "../../theme/typography";
import { StatusBadge } from "../status/status-badge";
import { cn } from "../../utils/cn";

export function ProcessingOverlay({
  active = false,
  label = "处理中…",
  className,
}: {
  active?: boolean;
  label?: string;
  className?: string;
}) {
  if (!active) return null;
  return (
    <div
      className={cn("absolute inset-0 z-[30] flex items-center justify-center", className)}
      style={{ backgroundColor: "rgba(15, 23, 42, 0.78)" }}
      role="status"
      aria-live="polite"
    >
      <div
        className="flex items-center gap-3 rounded border px-4 py-2"
        style={{
          borderColor: designTokens.colors.border.default,
          backgroundColor: designTokens.colors.background.panel,
          transition: `opacity ${interactionTokens.transition.fast}`,
        }}
      >
        <StatusBadge status="processing" label={label} pulse compact />
      </div>
    </div>
  );
}
