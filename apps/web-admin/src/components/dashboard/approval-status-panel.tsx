"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import { designTokens } from "@zhenhang/ui";
import type { PipelineItem } from "./types";

const STATE_LABELS: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
};

const STATE_COLORS: Record<string, string> = {
  draft: designTokens.colors.text.muted,
  reviewing: designTokens.colors.warning.default,
  approved: designTokens.colors.success.default,
};

export function ApprovalStatusPanel({ pipeline }: { pipeline: PipelineItem[] }) {
  const total = pipeline.reduce((s, p) => s + p.count, 0) || 1;
  const reviewing = pipeline.find((p) => p.state === "reviewing")?.count ?? 0;

  return (
    <IndustrialPanel title="审批状态">
      <div className="mb-4 flex items-center justify-between">
        <span className={typography.caption}>审批中</span>
        <span className={typography.kpi} style={{ fontSize: "1.25rem" }}>
          {reviewing}
        </span>
      </div>
      <ul className="space-y-3">
        {pipeline.map((p) => {
          const pct = Math.round((p.count / total) * 100);
          const color = STATE_COLORS[p.state] ?? designTokens.colors.primary.default;
          return (
            <li key={p.state}>
              <div className="mb-1 flex justify-between text-sm">
                <span className={typography.body}>{STATE_LABELS[p.state] ?? p.state}</span>
                <span className={typography.monoNumber}>
                  {p.count} · {pct}%
                </span>
              </div>
              <div
                className="h-2 overflow-hidden rounded-full"
                style={{ backgroundColor: designTokens.colors.border.muted }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </IndustrialPanel>
  );
}
