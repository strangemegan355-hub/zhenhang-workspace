"use client";

import {
  ChartSkeleton,
  designTokens,
  IndustrialPanel,
  KpiSkeleton,
  PanelSkeleton,
  typography,
} from "@zhenhang/ui";

export function DashboardSkeleton() {
  return (
    <div
      className="space-y-4"
      style={{ color: designTokens.colors.text.secondary }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <div className={`${typography.pageTitle} opacity-40`}>工作台</div>
          <div className={`${typography.caption} opacity-30`}>加载业务数据…</div>
        </div>
      </div>

      <KpiSkeleton count={6} compact />

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 space-y-4 2xl:col-span-8">
          <div className="grid gap-4 lg:grid-cols-3">
            <IndustrialPanel title="报价趋势" loading />
            <IndustrialPanel title="审批状态" loading />
            <IndustrialPanel title="导出任务" loading />
          </div>
        </div>
        <div className="col-span-12 space-y-4 2xl:col-span-4">
          <IndustrialPanel title="实时通知" loading />
          <IndustrialPanel title="风险预警" loading />
          <IndustrialPanel title="系统状态" loading />
        </div>
        <div className="col-span-12 grid gap-4 lg:grid-cols-3">
          <IndustrialPanel title="最近报价">
            <PanelSkeleton rows={5} />
          </IndustrialPanel>
          <IndustrialPanel title="车间状态">
            <ChartSkeleton height={120} />
          </IndustrialPanel>
          <IndustrialPanel title="快捷入口">
            <PanelSkeleton rows={4} />
          </IndustrialPanel>
        </div>
      </div>
    </div>
  );
}
