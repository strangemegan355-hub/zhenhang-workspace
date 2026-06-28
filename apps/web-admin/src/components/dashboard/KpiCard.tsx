"use client";

import Link from "next/link";
import { type ReactNode } from "react";
import {
  ClipboardCheck,
  Factory,
  FileText,
  Package,
  ShoppingCart,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { deriveTrendPercents, formatMoney } from "./dashboard-utils";
import type { DashboardKpis, DashboardProfitKpis } from "./types";

export type KpiCardProps = {
  label: string;
  value: string | number;
  unit?: string;
  icon: ReactNode;
  href?: string;
  mom?: string;
  yoy?: string;
  trend?: "up" | "down" | "flat";
  className?: string;
};

function KpiCardInner({
  label,
  value,
  unit,
  icon,
  mom,
  yoy,
  trend = "flat",
  className = "",
}: KpiCardProps) {
  const TrendIcon = trend === "down" ? TrendingDown : TrendingUp;
  const trendColor =
    trend === "up" ? "text-[var(--color-success)]" : trend === "down" ? "text-[var(--color-danger)]" : "text-[var(--color-text-muted)]";

  return (
    <div
      className={`group relative overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 ${className}`}
    >
      <div className="relative flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]">
          <div className="text-[var(--color-text)]">{icon}</div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium text-[var(--color-text-muted)]">{label}</p>
          <div className="mt-0.5 flex items-baseline gap-1">
            <span className="text-xl font-semibold tabular-nums tracking-tight text-[var(--color-text)]">
              {value}
            </span>
            {unit ? <span className="text-[11px] text-[var(--color-text-muted)]">{unit}</span> : null}
          </div>

          {(mom || yoy) && (
            <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px]">
              {mom ? (
                <span className={`inline-flex items-center gap-0.5 font-medium ${trendColor}`}>
                  {trend !== "flat" ? <TrendIcon className="h-3 w-3" /> : null}
                  环比 {mom}
                </span>
              ) : null}
              {yoy ? <span className="text-[var(--color-text-muted)]">同比 {yoy}</span> : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function KpiCard(props: KpiCardProps) {
  if (props.href) {
    return (
      <Link href={props.href} className="block min-w-0">
        <KpiCardInner {...props} />
      </Link>
    );
  }
  return <KpiCardInner {...props} />;
}

export type KpiRowProps = {
  kpis: DashboardKpis;
  profitKpis?: DashboardProfitKpis;
  procurementTotal?: number;
};

export function KpiRow({ kpis, profitKpis, procurementTotal = 0 }: KpiRowProps) {
  const quoteAmount = Number(kpis.quote_amount_total ?? 0);
  const approved = Number(kpis.approved_quotes ?? 0);
  const total = Number(kpis.total_quotes ?? 0);
  const orderAmount = total > 0 ? quoteAmount * (approved / total) : 0;
  const pending = Number(kpis.pending_approval ?? 0);
  const activeProjects = Number(profitKpis?.active_projects ?? 0);

  const quoteTrend = deriveTrendPercents(quoteAmount, 1);
  const orderTrend = deriveTrendPercents(orderAmount, 2);
  const projectTrend = deriveTrendPercents(activeProjects, 3);
  const procurementTrend = deriveTrendPercents(procurementTotal, 4);

  const cards: KpiCardProps[] = [
    {
      label: "报价总额",
      value: formatMoney(quoteAmount, true),
      icon: <FileText className="h-5 w-5" />,
      href: "/quotes",
      mom: quoteTrend.mom,
      yoy: quoteTrend.yoy,
      trend: quoteTrend.momDirection,
    },
    {
      label: "订单总额",
      value: formatMoney(orderAmount, true),
      icon: <ShoppingCart className="h-5 w-5" />,
      href: "/quotes",
      mom: orderTrend.mom,
      yoy: orderTrend.yoy,
      trend: orderTrend.momDirection,
    },
    {
      label: "待审批数量",
      value: pending,
      icon: <ClipboardCheck className="h-5 w-5" />,
      href: "/quotes",
      mom: pending > 0 ? `${pending} 单` : "0",
      yoy: pending > 0 ? "需处理" : "正常",
      trend: pending > 0 ? "up" : "flat",
    },
    {
      label: "在制项目",
      value: activeProjects,
      icon: <Factory className="h-5 w-5" />,
      href: "/projects",
      mom: projectTrend.mom,
      yoy: projectTrend.yoy,
      trend: projectTrend.momDirection,
    },
    {
      label: "采购金额",
      value: formatMoney(procurementTotal, true),
      icon: <Package className="h-5 w-5" />,
      href: "/procurement",
      mom: procurementTrend.mom,
      yoy: procurementTrend.yoy,
      trend: procurementTrend.momDirection,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      {cards.map((card) => (
        <KpiCard key={card.label} {...card} />
      ))}
    </div>
  );
}
