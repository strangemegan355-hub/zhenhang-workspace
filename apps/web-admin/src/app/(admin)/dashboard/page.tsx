"use client";

import { useDashboardOverviewQuery } from "@zhenhang/query-hooks";
import { ErrorBanner, IndustrialPage, InlineLoadingBar, typography } from "@zhenhang/ui";
import { DashboardKpiRow } from "@/components/dashboard/dashboard-kpi-row";
import { DashboardRealtimeStatusBar } from "@/components/dashboard/dashboard-realtime-status-bar";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { ApprovalStatusPanel } from "@/components/dashboard/approval-status-panel";
import { ExportStatusPanel } from "@/components/dashboard/export-status-panel";
import { QuoteTrendPanel } from "@/components/dashboard/quote-trend-panel";
import { RealtimeNotificationsPanel } from "@/components/dashboard/realtime-notifications-panel";
import { RecentQuotesPanel } from "@/components/dashboard/recent-quotes-panel";
import { QuickActionsPanel } from "@/components/dashboard/quick-actions-panel";
import { RiskCenterPanel } from "@/components/dashboard/risk-center-panel";
import { SystemStatusPanel } from "@/components/dashboard/system-status-panel";
import { WorkshopStatusPanel } from "@/components/dashboard/workshop-status-panel";
import type { DashboardKpis, PipelineItem, RecentQuote } from "@/components/dashboard/types";
import { useAuthStore } from "@/store/auth-store";
import Link from "next/link";
import { useEffect, useState } from "react";

type MetricsSnap = {
  uptime_seconds?: number;
  api?: { error_rate?: number };
  realtime?: { ws_connections_active?: number; sse_connections_active?: number; events_hot_count?: number };
  export?: { failures_total?: number };
  worker?: { queue_backlog_pending?: number };
};

export default function DashboardPage() {
  const { data, isLoading, isError, isFetching, refetch } = useDashboardOverviewQuery();
  const token = useAuthStore((s) => s.token?.accessToken);
  const [metrics, setMetrics] = useState<MetricsSnap | null>(null);

  useEffect(() => {
    if (!token) return;
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    let cancelled = false;

    const load = async () => {
      try {
        const resp = await fetch(`${apiBase}/api/v1/health/metrics`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!resp.ok) return;
        const json = await resp.json();
        const snap = (json?.data ?? json) as MetricsSnap;
        if (!cancelled) setMetrics(snap);
      } catch {
        /* optional */
      }
    };

    void load();
    const id = window.setInterval(() => void load(), 60000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [token]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError) {
    return <ErrorBanner message="?????????" onRetry={() => refetch()} />;
  }

  const overview = data as Record<string, unknown> | undefined;
  const kpis = (overview?.kpis ?? {}) as DashboardKpis;
  const pipeline = (overview?.pipeline ?? []) as PipelineItem[];
  const recent = (overview?.recent_quotes ?? []) as RecentQuote[];
  const generatedAt = String(overview?.generated_at ?? "").replace("T", " ").slice(0, 19);

  const exportFailures = metrics?.export?.failures_total ?? 0;
  const wsConnections =
    (metrics?.realtime?.ws_connections_active ?? 0) + (metrics?.realtime?.sse_connections_active ?? 0);

  return (
    <IndustrialPage gap="md" className="relative">
      <InlineLoadingBar active={isFetching} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className={typography.pageTitle}>???????</h1>
          <p className={typography.caption}>???? {generatedAt || "\u2014"}</p>
        </div>
        <Link
          href="/quotes/new"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-700"
        >
          ????
        </Link>
      </div>

      <DashboardRealtimeStatusBar exportPending={Number(kpis.export_pending ?? 0)} />
      <DashboardKpiRow kpis={kpis} />

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 flex flex-col gap-4 2xl:col-span-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <QuoteTrendPanel pipeline={pipeline} />
            <ApprovalStatusPanel pipeline={pipeline} />
            <ExportStatusPanel
              exportPending={Number(kpis.export_pending ?? 0)}
              exportFailures={exportFailures}
            />
          </div>
        </div>

        <div className="col-span-12 flex flex-col gap-4 2xl:col-span-4">
          <RealtimeNotificationsPanel unreadCount={Number(kpis.unread_notifications ?? 0)} />
          <RiskCenterPanel kpis={kpis} />
          <SystemStatusPanel
            apiUptimeSeconds={metrics?.uptime_seconds ?? 0}
            errorRate={metrics?.api?.error_rate ?? 0}
            wsConnections={wsConnections}
            hotEvents={metrics?.realtime?.events_hot_count ?? 0}
          />
        </div>

        <div className="col-span-12 grid gap-4 lg:grid-cols-3">
          <RecentQuotesPanel recent={recent} />
          <WorkshopStatusPanel />
          <QuickActionsPanel />
        </div>
      </div>
    </IndustrialPage>
  );
}
