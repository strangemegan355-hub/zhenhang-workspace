import { designTokens } from "../../theme/design-tokens";
import { ShimmerBlock } from "./shimmer";

export function KpiSkeleton({ count = 6, compact = false }: { count?: number; compact?: boolean }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={compact ? "rounded-lg border p-3" : "rounded-lg border p-4"}
          style={{
            borderColor: designTokens.colors.border.default,
            backgroundColor: designTokens.colors.background.elevated,
            borderLeftWidth: "3px",
            borderLeftColor: designTokens.colors.border.muted,
          }}
        >
          <ShimmerBlock className="h-3 w-1/2" />
          <ShimmerBlock className={compact ? "mt-2 h-6 w-2/3" : "mt-3 h-8 w-2/3"} />
          <ShimmerBlock className="mt-2 h-3 w-1/3" />
        </div>
      ))}
    </div>
  );
}
