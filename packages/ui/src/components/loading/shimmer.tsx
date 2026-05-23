import type { CSSProperties } from "react";
import { designTokens } from "../../theme/design-tokens";
import { cn } from "../../utils/cn";

export function ShimmerBlock({ className, style }: { className?: string; style?: CSSProperties }) {
  return (
    <div
      className={cn("animate-pulse rounded-md", className)}
      style={{
        backgroundColor: designTokens.colors.border.muted,
        ...style,
      }}
    />
  );
}
