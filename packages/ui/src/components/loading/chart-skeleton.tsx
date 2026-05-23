import { designTokens } from "../../theme/design-tokens";
import { ShimmerBlock } from "./shimmer";

export function ChartSkeleton({ height = 160 }: { height?: number }) {
  const bars = [40, 65, 45, 80, 55, 70, 50, 90, 60, 75];
  return (
    <div className="space-y-3">
      <ShimmerBlock className="h-3 w-24" />
      <div className="flex items-end gap-2" style={{ height }}>
        {bars.map((pct, i) => (
          <ShimmerBlock
            key={i}
            className="flex-1 rounded-t-sm"
            style={{
              height: `${pct}%`,
              backgroundColor: designTokens.colors.border.muted,
            }}
          />
        ))}
      </div>
    </div>
  );
}
