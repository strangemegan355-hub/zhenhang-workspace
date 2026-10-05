import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../src/components/dashboard");

function u(s) {
  return s.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
}

const files = {
  "SalesOverviewPanel.tsx": String.raw`"use client";

import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { buildMonthlyTrends } from "./dashboard-utils";
import type { DashboardKpis, RecentQuote } from "./types";

export function SalesOverviewPanel({ recent, kpis }: { recent: RecentQuote[]; kpis: DashboardKpis }) {
  const [activeTab, setActiveTab] = useState<"all" | "quotes" | "orders">("all");
  const data = useMemo(() => buildMonthlyTrends(recent, kpis), [recent, kpis]);
  const totalQuotes = data.reduce((s, d) => s + d.quotes, 0);
  const totalOrders = data.reduce((s, d) => s + d.orders, 0);

  return (
    <DashboardCard
      title="\u9500\u552e\u63a7\u5236\u4e2d\u5fc3"
      fill
      toolbar={
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-primary-soft)] px-2.5 py-1 text-[11px] font-medium text-[var(--color-text)]">
            <TrendingUp className="h-3 w-3" />
            \u8fd1 6 \u6708
          </span>
          <div className="flex rounded border border-[var(--color-border)] p-0.5 text-[11px]">
            {([["all", "\u5168\u90e8"], ["quotes", "\u62a5\u4ef7"], ["orders", "\u8ba2\u5355"]] as const).map(([key, label]) => (
              <button key={key} type="button" onClick={() => setActiveTab(key)} className={\`rounded px-2.5 py-1 \${activeTab === key ? "bg-[var(--color-primary)] text-white" : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"}\`}>{label}</button>
            ))}
          </div>
        </div>
      }
      contentClassName="flex flex-col"
    >
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div><span className="text-[var(--color-text-muted)]">\u62a5\u4ef7\u7d2f\u8ba1 </span><span className="font-semibold tabular-nums text-[var(--color-text)]">{totalQuotes}</span></div>
        <div><span className="text-[var(--color-text-muted)]">\u8ba2\u5355\u7d2f\u8ba1 </span><span className="font-semibold tabular-nums text-[var(--color-text)]">{totalOrders}</span></div>
      </div>
      <div className="min-h-[400px] flex-1">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
            <defs>
              <linearGradient id="quoteGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#171717" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#171717" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="orderGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6c7680" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#6c7680" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#d1d8dd" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "#6c7680", fontSize: 12 }} axisLine={{ stroke: "#d1d8dd" }} tickLine={false} />
            <YAxis tick={{ fill: "#6c7680", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={{ borderRadius: 6, border: "1px solid #d1d8dd", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            {(activeTab === "all" || activeTab === "quotes") && (
              <Area type="monotone" dataKey="quotes" name="\u6708\u5ea6\u62a5\u4ef7" stroke="#171717" strokeWidth={2} fill="url(#quoteGradient)" dot={{ r: 3, fill: "#171717", strokeWidth: 0 }} activeDot={{ r: 5 }} />
            )}
            {(activeTab === "all" || activeTab === "orders") && (
              <Area type="monotone" dataKey="orders" name="\u6708\u5ea6\u8ba2\u5355" stroke="#6c7680" strokeWidth={2} fill="url(#orderGradient)" dot={{ r: 3, fill: "#6c7680", strokeWidth: 0 }} activeDot={{ r: 5 }} />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </DashboardCard>
  );
}
`,

  "WorkflowProgressCard.tsx": String.raw`"use client";

import { CheckCircle2, Circle, Clock3 } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import type { PipelineItem, WorkflowNode } from "./types";

function buildWorkflowNodes(pipeline: PipelineItem[]): WorkflowNode[] {
  const reviewing = pipeline.find((p) => p.state === "reviewing")?.count ?? 0;
  const approved = pipeline.find((p) => p.state === "approved")?.count ?? 0;
  const draft = pipeline.find((p) => p.state === "draft")?.count ?? 0;
  const inFlow = reviewing > 0 || approved > 0;
  return [
    { key: "start", label: "\u53d1\u8d77", approver: "\u4e1a\u52a1\u5458", time: draft > 0 ? "\u8fdb\u884c\u4e2d" : "\u5df2\u5b8c\u6210", state: inFlow || approved > 0 ? "done" : draft > 0 ? "active" : "pending" },
    { key: "dept", label: "\u90e8\u95e8\u5ba1\u6279", approver: "\u90e8\u95e8\u7ecf\u7406", time: reviewing > 0 ? "\u5904\u7406\u4e2d" : approved > 0 ? "\u5df2\u901a\u8fc7" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "active" : "pending" },
    { key: "gm", label: "\u603b\u7ecf\u7406\u5ba1\u6279", approver: "\u603b\u7ecf\u7406", time: reviewing > 0 ? "\u6392\u961f\u4e2d" : approved > 0 ? "\u5df2\u901a\u8fc7" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "active" : "pending" },
    { key: "finance", label: "\u8d22\u52a1\u5ba1\u6279", approver: "\u8d22\u52a1", time: approved > 0 ? "\u5df2\u901a\u8fc7" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "pending" : "pending" },
    { key: "done", label: "\u5b8c\u6210", approver: "\u7cfb\u7edf", time: approved > 0 ? \`\${approved} \u5355\` : undefined, state: approved > 0 ? "done" : "pending" },
  ];
}

function NodeIcon({ state }: { state: WorkflowNode["state"] }) {
  if (state === "done") return <CheckCircle2 className="h-5 w-5 text-[#22c55e]" />;
  if (state === "active") return <Clock3 className="h-5 w-5 animate-pulse text-[var(--color-primary)]" />;
  return <Circle className="h-5 w-5 text-[#cbd5e1]" />;
}

export function WorkflowProgressCard({ pipeline }: { pipeline: PipelineItem[] }) {
  const nodes = buildWorkflowNodes(pipeline);
  return (
    <DashboardCard title="\u5ba1\u6279\u6d41\u7a0b\u8fdb\u5ea6">
      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-[640px] items-start justify-between gap-2">
          {nodes.map((node, idx) => (
            <div key={node.key} className="flex flex-1 flex-col items-center">
              <div className="relative flex w-full items-center justify-center">
                {idx > 0 ? <div className={\`absolute right-1/2 top-1/2 h-0.5 w-full -translate-y-1/2 \${node.state === "pending" && nodes[idx - 1]?.state === "pending" ? "bg-[var(--color-border)]" : "bg-[var(--color-primary)]/40"}\`} style={{ width: "100%", left: "-50%" }} /> : null}
                <div className={\`relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 bg-[var(--color-surface)] \${node.state === "done" ? "border-[#22c55e]" : node.state === "active" ? "border-[var(--color-primary)]" : "border-[var(--color-border)]"}\`}><NodeIcon state={node.state} /></div>
              </div>
              <p className="mt-2 text-center text-xs font-semibold text-[var(--color-text)]">{node.label}</p>
              <p className="mt-0.5 text-center text-[10px] text-[var(--color-text-muted)]">{node.approver}</p>
              {node.time ? <p className="mt-0.5 text-center text-[10px] font-medium text-[var(--color-primary)]">{node.time}</p> : null}
            </div>
          ))}
        </div>
      </div>
    </DashboardCard>
  );
}
`,

  "SystemStatusCard.tsx": String.raw`"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { healthFromErrorRate, healthFromLatency, type ServiceHealth } from "./dashboard-utils";

type ReadySnap = { db?: { status?: string; latency_ms?: number }; redis?: { status?: string; latency_ms?: number } };
type MetricsSnap = { api?: { error_rate?: number }; realtime?: { ws_connections_active?: number; sse_connections_active?: number }; worker?: { queue_backlog_pending?: number } };
type ServiceRow = { key: string; label: string; health: ServiceHealth; detail: string };

const HEALTH_DOT: Record<ServiceHealth, string> = { healthy: "bg-[#22c55e]", warning: "bg-[#f59e0b] animate-pulse", error: "bg-[#ef4444] animate-pulse" };
const HEALTH_LABEL: Record<ServiceHealth, string> = { healthy: "\u6b63\u5e38", warning: "\u8b66\u544a", error: "\u5f02\u5e38" };

export function SystemStatusCard({ metrics, token }: { metrics?: MetricsSnap | null; token?: string | null }) {
  const [ready, setReady] = useState<ReadySnap | null>(null);
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await fetch(\`\${apiBase}/api/v1/health/ready\`);
        if (!resp.ok) return;
        const json = await resp.json();
        if (!cancelled) setReady((json?.data ?? json) as ReadySnap);
      } catch { /* optional */ }
    };
    void load();
    const id = window.setInterval(() => void load(), 60000);
    return () => { cancelled = true; window.clearInterval(id); };
  }, [token]);

  const errorRate = metrics?.api?.error_rate ?? 0;
  const wsConnections = (metrics?.realtime?.ws_connections_active ?? 0) + (metrics?.realtime?.sse_connections_active ?? 0);
  const workerBacklog = metrics?.worker?.queue_backlog_pending ?? 0;
  const apiHealth = healthFromErrorRate(errorRate);
  const pgHealth = ready?.db?.status === "up" ? healthFromLatency(ready.db.latency_ms) : ("warning" as const);
  const redisHealth = ready?.redis?.status === "up" ? healthFromLatency(ready.redis.latency_ms) : ("warning" as const);
  const wsHealth: ServiceHealth = wsConnections > 0 ? "healthy" : token ? "warning" : "healthy";
  const workerHealth: ServiceHealth = workerBacklog > 50 ? "error" : workerBacklog > 10 ? "warning" : "healthy";
  const minioHealth: ServiceHealth = apiHealth === "error" ? "warning" : "healthy";

  const services: ServiceRow[] = [
    { key: "api", label: "API", health: apiHealth, detail: errorRate < 0.05 ? "\u54cd\u5e94\u6b63\u5e38" : \`\u9519\u8bef\u7387 \${(errorRate * 100).toFixed(1)}%\` },
    { key: "postgres", label: "PostgreSQL", health: pgHealth, detail: ready?.db?.latency_ms != null ? \`\${ready.db.latency_ms} ms\` : "\u68c0\u6d4b\u4e2d" },
    { key: "redis", label: "Redis", health: redisHealth, detail: ready?.redis?.latency_ms != null ? \`\${ready.redis.latency_ms} ms\` : "\u68c0\u6d4b\u4e2d" },
    { key: "minio", label: "MinIO", health: minioHealth, detail: "\u5bf9\u8c61\u5b58\u50a8" },
    { key: "worker", label: "Worker", health: workerHealth, detail: workerBacklog > 0 ? \`\u961f\u5217 \${workerBacklog}\` : "\u7a7a\u95f2" },
    { key: "websocket", label: "WebSocket", health: wsHealth, detail: \`\${wsConnections} \u8fde\u63a5\` },
  ];

  return (
    <DashboardCard title="\u7cfb\u7edf\u72b6\u6001" toolbar={<span className="flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]"><RefreshCw className="h-3 w-3" />60s \u5237\u65b0</span>}>
      <div className="grid gap-2 sm:grid-cols-2">
        {services.map((svc) => (
          <div key={svc.key} className="flex items-center gap-3 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2.5">
            <span className={\`h-2.5 w-2.5 shrink-0 rounded-full \${HEALTH_DOT[svc.health]}\`} />
            <div className="min-w-0 flex-1"><p className="text-xs font-medium text-[var(--color-text)]">{svc.label}</p><p className="text-[11px] text-[var(--color-text-muted)]">{svc.detail}</p></div>
            <span className={\`shrink-0 text-[10px] font-semibold \${svc.health === "healthy" ? "text-[#22c55e]" : svc.health === "warning" ? "text-[#f59e0b]" : "text-[#ef4444]"}\`}>{HEALTH_LABEL[svc.health]}</span>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
`,

  "RecentQuotesCard.tsx": String.raw`"use client";

import Link from "next/link";
import { StatusBadge, workflowStateToStatus } from "@zhenhang/ui";
import { ArrowUpRight, FileText } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";
import type { RecentQuote } from "./types";

const STATE_LABELS: Record<string, string> = { draft: "\u8349\u7a3f", reviewing: "\u5ba1\u6838\u4e2d", approved: "\u5df2\u6279\u51c6", rejected: "\u5df2\u9a73\u56de" };

export function RecentQuotesCard({ recent = [] }: { recent?: RecentQuote[] }) {
  const items = recent.slice(0, 5);
  return (
    <DashboardCard title="\u6700\u8fd1\u62a5\u4ef7" toolbar={<Link href="/quotes" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u5168\u90e8<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u62a5\u4ef7\u8bb0\u5f55</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const state = item.workflow_state ?? "draft";
          return (
            <li key={item.id ?? item.quote_no}>
              <Link href={\`/quotes/\${item.id ?? ""}\`} className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><FileText className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-[var(--color-text)]">{item.quote_no ?? item.title ?? "\u62a5\u4ef7"}</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(item.updated_at ?? item.created_at)}</p>
                  </div>
                </div>
                <StatusBadge status={workflowStateToStatus(state)} label={STATE_LABELS[state] ?? state} compact />
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
`,

  "NotificationCenterCard.tsx": String.raw`"use client";

import Link from "next/link";
import { useNotificationsQuery, useNotificationUnreadCountQuery } from "@zhenhang/query-hooks";
import { Bell, ArrowUpRight } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

export function NotificationCenterCard() {
  const unreadQuery = useNotificationUnreadCountQuery();
  const listQuery = useNotificationsQuery({ page: 1, unreadOnly: false });
  const unreadCount = unreadQuery.data ?? 0;
  const items = ((listQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).slice(0, 5);
  return (
    <DashboardCard title="\u901a\u77e5\u4e2d\u5fc3" toolbar={<Link href="/notifications" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u6d88\u606f\u4e2d\u5fc3{unreadCount > 0 ? \` (\${unreadCount})\` : ""}<ArrowUpRight className="h-3 w-3" /></Link>}>
      {listQuery.isLoading && !items.length ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u52a0\u8f7d\u4e2d\u2026</p> : items.length === 0 ? (
        <div className="flex flex-col items-center py-8 text-center"><Bell className="mb-2 h-8 w-8 text-[#cbd5e1]" /><p className="text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u901a\u77e5</p></div>
      ) : (
        <ul className="space-y-1">{items.map((row) => {
          const id = String(row.id ?? "");
          const isUnread = !row.read_at && String(row.status ?? "") !== "read";
          return (
            <li key={id}>
              <Link href="/notifications" className={\`flex items-start justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)] \${isUnread ? "bg-[var(--color-surface-soft)]" : ""}\`}>
                <div className="min-w-0 flex-1">
                  <p className={\`truncate text-xs text-[var(--color-text)] \${isUnread ? "font-semibold" : "font-medium"}\`}>{String(row.title ?? "\u901a\u77e5")}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{String(row.channel ?? row.biz_type ?? "system")}</p>
                </div>
                <span className="shrink-0 text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(row.created_at ?? ""))}</span>
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}

export function RecentActivityCard() {
  const listQuery = useNotificationsQuery({ page: 1, unreadOnly: false });
  const items = ((listQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).slice(0, 6);
  return (
    <DashboardCard title="\u6700\u8fd1\u6d3b\u52a8" toolbar={<Link href="/notifications" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u67e5\u770b\u5168\u90e8<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u6d3b\u52a8\u8bb0\u5f55</p> : (
        <ul className="relative space-y-0 pl-3">
          <div className="absolute bottom-2 left-[7px] top-2 w-px bg-[var(--color-border)]" />
          {items.map((row, idx) => (
            <li key={String(row.id ?? idx)} className="relative pb-3 last:pb-0">
              <span className="absolute -left-3 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-[var(--color-primary)]" />
              <div className="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2">
                <p className="text-xs font-medium text-[var(--color-text)]">{String(row.title ?? "\u7cfb\u7edf\u6d3b\u52a8")}</p>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(row.created_at ?? ""))} \u00b7 {String(row.channel ?? row.biz_type ?? "system")}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </DashboardCard>
  );
}
`,

  "RiskCenterCard.tsx": String.raw`"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import type { DashboardKpis, DashboardProfitKpis, RiskItem } from "./types";

function buildRisks(kpis: DashboardKpis, profitKpis?: DashboardProfitKpis): RiskItem[] {
  const items: RiskItem[] = [];
  const pending = Number(kpis.pending_approval ?? 0);
  const exportPending = Number(kpis.export_pending ?? 0);
  const overBudget = Number(profitKpis?.over_budget_count ?? 0);
  if (overBudget > 0) items.push({ id: "material-missing", label: "\u6750\u6599\u7f3a\u5931", level: overBudget >= 3 ? "high" : "medium", count: overBudget, detail: \`\${overBudget} \u4e2a\u9879\u76ee BOM/\u6210\u672c\u672a\u9f50\u5957\`, href: "/order-profit" });
  if (pending > 0) items.push({ id: "approval-timeout", label: "\u5ba1\u6279\u8d85\u65f6", level: pending >= 5 ? "high" : "medium", count: pending, detail: \`\${pending} \u5355\u8d85\u65f6 SLA \u5f85\u5904\u7406\`, href: "/quotes" });
  if (exportPending > 0) items.push({ id: "procurement-delay", label: "\u91c7\u8d2d\u5ef6\u671f", level: exportPending >= 3 ? "high" : "medium", count: exportPending, detail: \`\${exportPending} \u9879\u91c7\u8d2d/\u5bfc\u51fa\u6392\u961f\`, href: "/procurement" });
  items.push({ id: "customer-debt", label: "\u5ba2\u6237\u6b20\u6b3e", level: Number(kpis.draft_quotes ?? 0) > 3 ? "medium" : "low", count: Number(kpis.draft_quotes ?? 0), detail: "\u8349\u7a3f\u62a5\u4ef7\u672a\u8f6c\u5355", href: "/customers" });
  return items.slice(0, 5);
}

const LEVEL_TAG: Record<RiskItem["level"], { label: string; className: string }> = {
  high: { label: "\u9ad8\u98ce\u9669", className: "bg-[#fde8e8] text-[#ef4444]" },
  medium: { label: "\u4e2d\u98ce\u9669", className: "bg-[#fff8e6] text-[#d97706]" },
  low: { label: "\u4f4e\u98ce\u9669", className: "bg-[var(--color-primary-soft)] text-[var(--color-primary)]" },
};

export function RiskCenterCard({ kpis, profitKpis }: { kpis?: DashboardKpis; profitKpis?: DashboardProfitKpis }) {
  const risks = kpis ? buildRisks(kpis, profitKpis) : [];
  return (
    <DashboardCard title="\u98ce\u9669\u9884\u8b66" toolbar={<span className="inline-flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]"><AlertTriangle className="h-3 w-3" />\u5b9e\u65f6\u76d1\u6d4b</span>}>
      {risks.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u5f53\u524d\u65e0\u663e\u8457\u98ce\u9669\u9879</p> : (
        <ul className="space-y-2">{risks.map((risk) => {
          const tag = LEVEL_TAG[risk.level];
          const row = (
            <li className="flex items-center justify-between gap-3 rounded border border-[var(--color-border)] px-3 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2"><span className={\`rounded-full px-2 py-0.5 text-[10px] font-semibold \${tag.className}\`}>{tag.label}</span><span className="text-xs font-medium text-[var(--color-text)]">{risk.label}</span></div>
                {risk.detail ? <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">{risk.detail}</p> : null}
              </div>
              {risk.count != null ? <span className="shrink-0 text-sm font-semibold tabular-nums text-[var(--color-text)]">{risk.count}</span> : null}
            </li>
          );
          return risk.href ? <Link key={risk.id} href={risk.href} className="block">{row}</Link> : <div key={risk.id}>{row}</div>;
        })}</ul>
      )}
    </DashboardCard>
  );
}
`,

  "RecentProjectsCard.tsx": String.raw`"use client";

import Link from "next/link";
import { useProjectsQuery } from "@zhenhang/query-hooks";
import { ArrowUpRight, FolderKanban } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

const STAGE_LABELS: Record<string, string> = { lead: "\u7ebf\u7d22", quote: "\u62a5\u4ef7", contract: "\u5408\u540c", production: "\u751f\u4ea7", delivery: "\u4ea4\u4ed8", closed: "\u7ed3\u6848" };
const STAGE_STYLES: Record<string, string> = { lead: "bg-[#f1f5f9] text-[#64748b]", quote: "bg-[var(--color-primary-soft)] text-[var(--color-primary)]", contract: "bg-[#f0fdf4] text-[#16a34a]", production: "bg-[#fff8e6] text-[#d97706]", delivery: "bg-[#faf5ff] text-[#7c3aed]", closed: "bg-[#f1f5f9] text-[#475569]" };

export function RecentProjectsCard() {
  const { data } = useProjectsQuery(1);
  const items = ((data?.items ?? []) as Record<string, unknown>[]).slice(0, 5);
  return (
    <DashboardCard title="\u6700\u8fd1\u9879\u76ee" toolbar={<Link href="/projects" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u5168\u90e8<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u9879\u76ee</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const stage = String(item.stage ?? "lead");
          return (
            <li key={String(item.id ?? item.project_no)}>
              <Link href="/projects" className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><FolderKanban className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0"><p className="truncate text-xs font-medium text-[var(--color-text)]">{String(item.name ?? item.project_no ?? "\u9879\u76ee")}</p><p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(item.updated_at ?? item.created_at ?? ""))}</p></div>
                </div>
                <span className={\`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium \${STAGE_STYLES[stage] ?? STAGE_STYLES.lead}\`}>{STAGE_LABELS[stage] ?? stage}</span>
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
`,

  "RecentWorkOrdersCard.tsx": String.raw`"use client";

import Link from "next/link";
import { useWorkOrdersQuery } from "@zhenhang/query-hooks";
import { ArrowUpRight, Wrench } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

const STATUS_LABELS: Record<string, string> = { todo: "\u5f85\u5f00\u5de5", doing: "\u8fdb\u884c\u4e2d", done: "\u5df2\u5b8c\u6210", exception: "\u5f02\u5e38" };
const STATUS_STYLES: Record<string, string> = { todo: "bg-[#f1f5f9] text-[#64748b]", doing: "bg-[var(--color-primary-soft)] text-[var(--color-primary)]", done: "bg-[#f0fdf4] text-[#16a34a]", exception: "bg-[#fde8e8] text-[#ef4444]" };

export function RecentWorkOrdersCard() {
  const { data } = useWorkOrdersQuery(1);
  const items = ((data?.items ?? []) as Record<string, unknown>[]).slice(0, 5);
  return (
    <DashboardCard title="\u6700\u8fd1\u5de5\u5355" toolbar={<Link href="/work-orders" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u5168\u90e8<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u5de5\u5355</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const status = String(item.status ?? "todo");
          return (
            <li key={String(item.id ?? item.work_order_no)}>
              <Link href="/work-orders" className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><Wrench className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0"><p className="truncate text-xs font-medium text-[var(--color-text)]">{String(item.work_order_no ?? item.task_desc ?? "\u5de5\u5355")}</p><p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(item.updated_at ?? item.created_at ?? ""))}</p></div>
                </div>
                <span className={\`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium \${STATUS_STYLES[status] ?? STATUS_STYLES.todo}\`}>{STATUS_LABELS[status] ?? status}</span>
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
`,

  "RecentFilesCard.tsx": String.raw`"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { ArrowUpRight, Download, Eye, FileImage, FileSpreadsheet, FileText, PenTool } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

type FileRow = { id: string; file_name: string; file_ext?: string | null; mime_type?: string | null; created_at?: string };

function fileKind(ext?: string | null, mime?: string | null) {
  const e = (ext ?? mime ?? "").toLowerCase();
  if (e.includes("pdf")) return { label: "PDF", icon: FileText, color: "text-[#ef4444] bg-[#fef2f2]" };
  if (e.includes("xls") || e.includes("csv")) return { label: "Excel", icon: FileSpreadsheet, color: "text-[#16a34a] bg-[#f0fdf4]" };
  if (e.includes("dwg") || e.includes("cad") || e.includes("dxf")) return { label: "CAD", icon: PenTool, color: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]" };
  if (e.includes("jpg") || e.includes("png") || e.includes("jpeg") || e.includes("image")) return { label: "\u56fe\u7247", icon: FileImage, color: "text-[#7c3aed] bg-[#faf5ff]" };
  return { label: "\u6587\u4ef6", icon: FileText, color: "text-[#64748b] bg-[#f1f5f9]" };
}

export function RecentFilesCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "recent-files"],
    queryFn: async () => {
      const { data: resp } = await apiClient.get<{ data: { items?: FileRow[] } }>("/api/v1/files", { params: { page: 1, page_size: 5 } });
      return resp.data?.items ?? [];
    },
    staleTime: 60_000,
    retry: 1,
  });
  const items = data ?? [];
  return (
    <DashboardCard title="\u6587\u4ef6\u4e2d\u5fc3" toolbar={<Link href="/files" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">\u5168\u90e8\u6587\u4ef6<ArrowUpRight className="h-3 w-3" /></Link>}>
      {isLoading ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u52a0\u8f7d\u4e2d\u2026</p> : items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">\u6682\u65e0\u4e0a\u4f20\u6587\u4ef6</p> : (
        <ul className="space-y-2">{items.map((file) => {
          const kind = fileKind(file.file_ext, file.mime_type);
          const Icon = kind.icon;
          return (
            <li key={file.id} className="flex items-center gap-3 rounded border border-[var(--color-border)] px-3 py-2.5">
              <div className={\`flex h-9 w-9 shrink-0 items-center justify-center rounded \${kind.color}\`}><Icon className="h-4 w-4" /></div>
              <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-[var(--color-text)]">{file.file_name}</p><p className="text-[11px] text-[var(--color-text-muted)]">{kind.label} \u00b7 {formatRelativeTime(file.created_at)}</p></div>
              <div className="flex shrink-0 gap-1">
                <Link href={\`/files?preview=\${file.id}\`} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="\u67e5\u770b"><Eye className="h-4 w-4" /></Link>
                <a href={\`\${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/files/\${file.id}/download\`} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="\u4e0b\u8f7d"><Download className="h-4 w-4" /></a>
              </div>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
`,
};

for (const [name, raw] of Object.entries(files)) {
  fs.writeFileSync(path.join(dir, name), u(raw), "utf8");
  console.log("fixed", name);
}
