import { ShimmerBlock } from "./shimmer";

export function PanelSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      <ShimmerBlock className="h-4 w-1/3" />
      {Array.from({ length: rows }).map((_, i) => (
        <ShimmerBlock key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}
