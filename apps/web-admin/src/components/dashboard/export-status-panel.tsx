"use client";

import { IndustrialPanel, StatusBadge, typography } from "@zhenhang/ui";
import { designTokens } from "@zhenhang/ui";
import Link from "next/link";

export function ExportStatusPanel({
  exportPending = 0,
  exportFailures = 0,
}: {
  exportPending?: number;
  exportFailures?: number;
}) {
  const healthy = exportPending === 0 && exportFailures === 0;

  return (
    <IndustrialPanel
      title="导出任务"
      toolbar={
        <Link href="/quotes" className="text-xs text-blue-500 hover:underline">
          报价中心
        </Link>
      }
    >
      <div className="grid grid-cols-2 gap-3">
        <div
          className="rounded border p-3"
          style={{
            borderColor: designTokens.colors.border.default,
            backgroundColor: designTokens.colors.background.subtle,
          }}
        >
          <p className={typography.caption}>排队中</p>
          <p className={typography.kpi} style={{ fontSize: "1.25rem" }}>
            {exportPending}
          </p>
        </div>
        <div
          className="rounded border p-3"
          style={{
            borderColor: designTokens.colors.border.default,
            backgroundColor: designTokens.colors.background.subtle,
          }}
        >
          <p className={typography.caption}>失败累计</p>
          <p className={typography.kpi} style={{ fontSize: "1.25rem" }}>
            {exportFailures}
          </p>
        </div>
      </div>
      <div className="mt-3">
        <StatusBadge
          status={healthy ? "success" : exportFailures > 0 ? "danger" : "warning"}
          label={healthy ? "导出通道正常" : "存在待处理导出任务"}
          compact
          pulse={exportPending > 0}
        />
      </div>
    </IndustrialPanel>
  );
}
