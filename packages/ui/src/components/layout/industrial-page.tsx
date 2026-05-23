import type { ReactNode } from "react";
import { interactionTokens } from "../../theme/interaction-tokens";
import { cn } from "../../utils/cn";

/** Standard page vertical rhythm for dashboard / quotes / notifications */
export function IndustrialPage({
  children,
  className,
  gap = "md",
}: {
  children: ReactNode;
  className?: string;
  gap?: "sm" | "md" | "lg";
}) {
  const gapPx =
    gap === "sm"
      ? interactionTokens.layout.sectionGapSm
      : gap === "lg"
        ? interactionTokens.layout.sectionGapLg
        : interactionTokens.layout.sectionGapMd;

  return (
    <div className={cn("flex flex-col", className)} style={{ gap: gapPx }}>
      {children}
    </div>
  );
}
