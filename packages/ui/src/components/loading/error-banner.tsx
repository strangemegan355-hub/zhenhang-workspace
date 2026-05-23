"use client";

import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { typography } from "../../theme/typography";
import { statusPalette } from "../../theme/interaction-tokens";
import { cn } from "../../utils/cn";

export function ErrorBanner({
  message = "操作失败",
  onRetry,
  onDismiss,
  className,
}: {
  message?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}) {
  const palette = statusPalette("danger");
  return (
    <div
      className={cn("flex flex-wrap items-center justify-between gap-2 rounded border px-3 py-2 text-sm", className)}
      style={{
        borderColor: palette.border,
        backgroundColor: palette.bg,
        color: palette.fg,
        transition: `border-color ${interactionTokens.transition.fast}`,
      }}
      role="alert"
    >
      <span className={typography.body}>{message}</span>
      <div className="flex items-center gap-2">
        {onRetry ? (
          <button
            type="button"
            className={`${typography.caption} underline`}
            style={{ color: designTokens.colors.text.secondary }}
            onClick={onRetry}
          >
            重试
          </button>
        ) : null}
        {onDismiss ? (
          <button
            type="button"
            className={typography.caption}
            style={{ color: designTokens.colors.text.muted }}
            onClick={onDismiss}
          >
            关闭
          </button>
        ) : null}
      </div>
    </div>
  );
}
