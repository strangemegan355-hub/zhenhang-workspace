"use client";

import { useDashboardOverviewQuery, useProcurementEntriesQuery } from "@zhenhang/query-hooks";
import { ErrorBanner, InlineLoadingBar, typography } from "@zhenhang/ui";
import { useEffect, useMemo, useState } from "react";
import { ApprovalCenterCard } from "@/components/dashboard/ApprovalCenterCard";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { FinanceActionCard } from "@/components/dashboard/FinanceActionCard";
import { KpiRow } from "@/components/dashboard/KpiCard";
import { NotificationCenterCard, RecentActivityCard } from "@/components/dashboard/NotificationCenterCard";
import { QuickActionsCard } from "@/components/dashboard/QuickActionsCard";
import { RecentProjectsCard } from "@/components/dashboard/RecentProjectsCard";
import { RecentQuotesCard } from "@/components/dashboard/RecentQuotesCard";
import { RecentWorkOrdersCard } from "@/components/dashboard/RecentWorkOrdersCard";
import { RiskCenterCard } from "@/components/dashboard/RiskCenterCard";
import { SalesOverviewPanel } from "@/components/dashboard/SalesOverviewPanel";
import { SystemStatusCard } from "@/components/dashboard/SystemStatusCard";
import type {
  DashboardKpis,
  DashboardProfitKpis,
  RecentQuote,
} from "@/components/dashboard/types";
import { useAuthStore } from "@/store/auth-store";

type MetricsSnap = {
  uptime_seconds?: number;
  api?: { error_rate?: number };
  realtime?: { ws_connections_active?: number; sse_connections_active?: number; events_hot_count?: number };
  export?: { failures_total?: number };
  worker?: { queue_backlog_pending?: number };
};

export default function DashboardPage() {
  const { data, isLoading, isError, isFetching, refetch } = useDashboardOverviewQuery();
  const procurementQuery = useProcurementEntriesQuery(1);
  const token = useAuthStore((s) => s.token?.accessToken);
  const [metrics, setMetrics] = useState<MetricsSnap | null>(null);

  useEffect(() => {
    if (!token) return;
    // Prefer 127.0.0.1 on Windows: localhost can resolve to ::1 while API listens on IPv4.
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await fetch(`${apiBase}/api/v1/health/metrics`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!resp.ok) return;
        const json = await resp.json();
        if (!cancelled) setMetrics((json?.data ?? json) as MetricsSnap);
      } catch {
        /* metrics optional */
      }
    };
    void load();
    const id = window.setInterval(() => void load(), 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [token]);

  const procurementTotal = useMemo(() => {
    const items = (procurementQuery.data?.items ?? []) as Record<string, unknown>[];
    return items.reduce((sum, row) => sum + Number(row.qty ?? 0) * Number(row.unit_price ?? 0), 0);
  }, [procurementQuery.data]);

  if (isLoading) return <DashboardSkeleton />;
  if (isError) {
    return (
      <ErrorBanner
        message="无法加载看板数据。请确认后端 API 已启动，然后点击重试。"
        onRetry={() => refetch()}
      />
    );
  }

  const overview = data as Record<string, unknown> | undefined;
  const kpis = (overview?.kpis ?? {}) as DashboardKpis;
  const profitKpis = (overview?.profit_kpis ?? {}) as DashboardProfitKpis;
  const recentQuotes = (overview?.recent_quotes ?? []) as RecentQuote[];
  const generatedAt = String(overview?.generated_at ?? "").replace("T", " ").slice(0, 19);

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-4">
      <InlineLoadingBar active={isFetching} />

      <header className="space-y-0.5">
        <h1 className={`${typography.pageTitle} text-[var(--color-text)]`}>工作台</h1>
        <p className={`${typography.caption} text-[var(--color-text-muted)]`}>
          数据时间 {generatedAt || "—"} · 业务概览
        </p>
      </header>

      {/* UX-006：待办优先 — 审批 / 通知 / 财务入口置顶 */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <ApprovalCenterCard />
        <NotificationCenterCard />
        <FinanceActionCard />
      </div>

      <KpiRow kpis={kpis} profitKpis={profitKpis} procurementTotal={procurementTotal} />

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 space-y-4 xl:col-span-8">
          <SalesOverviewPanel recent={recentQuotes} kpis={kpis} />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <RecentQuotesCard recent={recentQuotes} />
            <RecentProjectsCard />
            <RecentWorkOrdersCard />
          </div>
        </div>
        <div className="col-span-12 space-y-4 xl:col-span-4">
          <RiskCenterCard kpis={kpis} profitKpis={profitKpis} />
          <QuickActionsCard />
          <RecentActivityCard />
          <SystemStatusCard metrics={metrics} token={token} />
        </div>
      </div>
    </div>
  );
}
