"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import { designTokens } from "@zhenhang/ui";
import type { PipelineItem } from "./types";

const STATE_LABELS: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
};

export function QuoteTrendPanel({ pipeline }: { pipeline: PipelineItem[] }) {
  const max = Math.max(...pipeline.map((p) => p.count), 1);
  const total = pipeline.reduce((s, p) => s + p.count, 0);

  return (
    <IndustrialPanel title="报价趋势" empty={pipeline.length === 0} emptyMessage="暂无流水线数据">
      <div className="mb-3 flex items-baseline justify-between">
        <span className={typography.caption}>近周期报价分布</span>
        <span className={typography.monoNumber}>{total} 单</span>
      </div>
      <div className="flex h-36 items-end gap-2">
        {pipeline.map((p) => {
          const pct = Math.round((p.count / max) * 100);
          return (
            <div key={p.state} className="flex min-w-0 flex-1 flex-col items-center gap-1">
              <div
                className="w-full rounded-t transition-all group-hover:opacity-90"
                style={{
                  height: `${Math.max(pct, 8)}%`,
                  backgroundColor: designTokens.colors.primary.default,
                  opacity: 0.85,
                }}
                title={`${STATE_LABELS[p.state] ?? p.state}: ${p.count}`}
              />
              <span className={`${typography.caption} truncate text-center`}>
                {STATE_LABELS[p.state] ?? p.state}
              </span>
              <span className={typography.monoNumber}>{p.count}</span>
            </div>
          );
        })}
      </div>
    </IndustrialPanel>
  );
}
