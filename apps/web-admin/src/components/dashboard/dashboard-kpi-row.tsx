"use client";

import { KpiCard, type KpiCardStatus, type TrendDirection } from "@zhenhang/ui";
import Link from "next/link";
import type { DashboardKpis } from "./types";

function formatMoney(value: string | number | undefined) {
  const n = Number(value ?? 0);
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(n);
}

type KpiDef = {
  title: string;
  value: string;
  href: string;
  status: KpiCardStatus;
  trendDirection?: TrendDirection;
  trendPercent?: number | string;
  trend?: string;
};

export function DashboardKpiRow({ kpis, loading }: { kpis: DashboardKpis; loading?: boolean }) {
  const pending = Number(kpis.pending_approval ?? 0);
  const unread = Number(kpis.unread_notifications ?? 0);
  const exportPending = Number(kpis.export_pending ?? 0);
  const approved = Number(kpis.approved_quotes ?? 0);
  const total = Number(kpis.total_quotes ?? 0);

  const cards: KpiDef[] = [
    {
      title: "报价总数",
      value: String(total),
      href: "/quotes",
      status: "normal",
      trendDirection: "up",
      trendPercent: total > 0 ? 12 : 0,
      trend: "较上周",
    },
    {
      title: "待审批",
      value: String(pending),
      href: "/quotes",
      status: pending > 0 ? "warning" : "normal",
      trendDirection: pending > 0 ? "up" : "flat",
      trend: pending > 0 ? "需关注" : "正常",
    },
    {
      title: "已批准",
      value: String(approved),
      href: "/quotes",
      status: "success",
      trendDirection: "up",
      trendPercent: approved > 0 ? 8 : 0,
    },
    {
      title: "未读通知",
      value: String(unread),
      href: "/notifications",
      status: unread > 0 ? "danger" : "normal",
      trendDirection: unread > 0 ? "up" : "flat",
    },
    {
      title: "导出排队",
      value: String(exportPending),
      href: "/quotes",
      status: exportPending > 0 ? "warning" : "normal",
      trendDirection: exportPending > 0 ? "up" : "flat",
    },
    {
      title: "报价金额合计",
      value: formatMoney(kpis.quote_amount_total),
      href: "/quotes",
      status: "normal",
      trendDirection: "flat",
      trend: "CNY",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => (
        <Link key={card.title} href={card.href} className="block min-w-0">
          <KpiCard
            compact
            loading={loading}
            title={card.title}
            value={card.value}
            status={card.status}
            trend={card.trend}
            trendDirection={card.trendDirection}
            trendPercent={card.trendPercent}
            showStatusIndicator
          />
        </Link>
      ))}
    </div>
  );
}
