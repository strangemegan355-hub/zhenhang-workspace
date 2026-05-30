import type { ReactNode } from "react";
import { interactionTokens } from "../../theme/interaction-tokens";
import { cn } from "../../utils/cn";

/** Standard page vertical rhythm for dashboard / quotes / notifications */
export function IndustrialPage({
  children,
  className,
  gap = "md",
  fill = false,
}: {
  children: ReactNode;
  className?: string;
  gap?: "sm" | "md" | "lg";
  /** Stretch to fill parent main workspace (list / master-data pages) */
  fill?: boolean;
}) {
  const gapPx =
    gap === "sm"
      ? interactionTokens.layout.sectionGapSm
      : gap === "lg"
        ? interactionTokens.layout.sectionGapLg
        : interactionTokens.layout.sectionGapMd;

  return (
    <div
      className={cn("flex flex-col", fill && "flex-1 min-h-[calc(100vh-5.5rem)]", className)}
      style={{ gap: gapPx }}
    >
      {children}
    </div>
  );
}
