"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { StatusBadge, riskLevelToStatus } from "@zhenhang/ui";
import { DashboardCard } from "./dashboard-card";
import type { DashboardKpis, DashboardProfitKpis, RiskItem } from "./types";

function buildRisks(kpis: DashboardKpis, profitKpis?: DashboardProfitKpis): RiskItem[] {
  const items: RiskItem[] = [];
  const pending = Number(kpis.pending_approval ?? 0);
  const exportPending = Number(kpis.export_pending ?? 0);
  const overBudget = Number(profitKpis?.over_budget_count ?? 0);
  if (overBudget > 0) items.push({ id: "material-missing", label: "材料缺失", level: overBudget >= 3 ? "high" : "medium", count: overBudget, detail: `${overBudget} 个项目 BOM/成本未齐套`, href: "/order-profit" });
  if (pending > 0) items.push({ id: "approval-timeout", label: "审批超时", level: pending >= 5 ? "high" : "medium", count: pending, detail: `${pending} 单超时 SLA 待处理`, href: "/quotes" });
  if (exportPending > 0) items.push({ id: "procurement-delay", label: "采购延期", level: exportPending >= 3 ? "high" : "medium", count: exportPending, detail: `${exportPending} 项采购/导出排队`, href: "/procurement" });
  items.push({ id: "customer-debt", label: "客户欠款", level: Number(kpis.draft_quotes ?? 0) > 3 ? "medium" : "low", count: Number(kpis.draft_quotes ?? 0), detail: "草稿报价未转单", href: "/customers" });
  return items.slice(0, 5);
}

const LEVEL_LABEL: Record<string, string> = { high: "高风险", medium: "中风险", low: "低风险" };

export function RiskCenterCard({ kpis, profitKpis }: { kpis?: DashboardKpis; profitKpis?: DashboardProfitKpis }) {
  const risks = kpis ? buildRisks(kpis, profitKpis) : [];
  return (
    <DashboardCard title="风险预警" toolbar={<span className="inline-flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]"><AlertTriangle className="h-3 w-3" />实时监测</span>}>
      {risks.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">当前无显著风险项</p> : (
        <ul className="space-y-2">{risks.map((risk) => {
          const row = (
            <li className="flex items-center justify-between gap-3 rounded border border-[var(--color-border)] px-3 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2"><StatusBadge status={riskLevelToStatus(risk.level)} label={LEVEL_LABEL[risk.level] ?? risk.level} compact /><span className="text-xs font-medium text-[var(--color-text)]">{risk.label}</span></div>
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
