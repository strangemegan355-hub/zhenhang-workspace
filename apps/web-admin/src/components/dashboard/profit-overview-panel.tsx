"use client";

import { IndustrialPanel, KpiCard, typography } from "@zhenhang/ui";
import Link from "next/link";
import type { DashboardProfitKpis, OverBudgetProjectItem } from "./types";

function money(n: string | number | null | undefined) {
  if (n == null || n === "") return "—";
  return Number(n).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function ProfitOverviewPanel({
  profitKpis,
  overBudgetTop3,
}: {
  profitKpis?: DashboardProfitKpis;
  overBudgetTop3?: OverBudgetProjectItem[];
}) {
  if (!profitKpis) return null;

  const overCount = Number(profitKpis.over_budget_count ?? 0);
  const variance = profitKpis.total_variance != null ? Number(profitKpis.total_variance) : null;
  const top3 = overBudgetTop3 ?? [];

  return (
    <IndustrialPanel
      title="项目利润概览"
      toolbar={
        <Link href="/order-profit" className="text-xs text-blue-400 hover:underline">
          查看订单利润
        </Link>
      }
    >
      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard compact title="在管项目" value={String(profitKpis.active_projects ?? 0)} status="normal" />
        <KpiCard
          compact
          title="超预算项目"
          value={String(overCount)}
          status={overCount > 0 ? "warning" : "success"}
        />
        <KpiCard compact title="实际毛利合计" value={money(profitKpis.total_realized_profit)} status="normal" />
        <KpiCard
          compact
          title="偏差合计"
          value={money(profitKpis.total_variance)}
          status={variance != null && variance > 0 ? "danger" : "normal"}
        />
      </div>

      {top3.length ? (
        <div>
          <h3 className={`${typography.cardTitle} mb-2`}>超预算 TOP3</h3>
          <ul className="space-y-2 text-xs">
            {top3.map((row) => (
              <li key={row.project_id} className="flex items-center justify-between gap-2 rounded border border-zinc-800 px-2 py-2">
                <div className="min-w-0">
                  <div className="font-medium text-zinc-200">
                    {row.project_no} · {row.name}
                  </div>
                  <div className="text-zinc-500">
                    预算 {money(row.budget_cost)} / 实际 {money(row.actual_cost_total)}
                  </div>
                </div>
                <span className="shrink-0 tabular-nums text-red-400">+{money(row.cost_variance)}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-xs text-zinc-500">暂无超预算项目；登记实际成本后将在此显示偏差排名。</p>
      )}
    </IndustrialPanel>
  );
}
