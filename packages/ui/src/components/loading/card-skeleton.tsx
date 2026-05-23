import { ShimmerBlock } from "./shimmer";

export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-lg border p-4"
          style={{
            borderColor: "#334155",
            backgroundColor: "#111827",
          }}
        >
          <ShimmerBlock className="mb-3 h-3 w-1/2" />
          <ShimmerBlock className="h-8 w-2/3" />
        </div>
      ))}
    </div>
  );
}
