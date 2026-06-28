"use client";

import { useProjectProfitLedgerQuery } from "@zhenhang/query-hooks";
import { MasterListPage } from "@/components/master/master-list-page";
import { IndustrialPage, IndustrialPanel, WorkspaceToolbarButton, typography } from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";
import { kpiCardClass, kpiCardLabelClass, kpiCardValueClass } from "@/lib/form-styles";

function KpiCard({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className={kpiCardClass}>
      <div className={kpiCardLabelClass}>{label}</div>
      <div className={`${kpiCardValueClass} ${tone ?? ""}`}>{value}</div>
    </div>
  );
}
type LedgerRow = {
  id: string;
  projectNo: string;
  name: string;
  stageLabel: string;
  ownerName: string;
  budgetCost: string;
  actualCost: string;
  variance: string;
  varianceTone: string;
  realizedProfit: string;
  budgetStatus: string;
  budgetStatusLabel: string;
};

const STAGE_LABEL: Record<string, string> = {
  lead: "线索",
  quoted: "已报价",
  ordered: "已下单",
  manufacturing: "生产中",
  delivery: "待交付",
  done: "已完成",
};

function money(n: unknown) {
  if (n == null || n === "") return "—";
  return Number(n).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function OrderProfitPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [overBudgetOnly, setOverBudgetOnly] = useState(false);

  const query = useProjectProfitLedgerQuery(page, search.trim() || undefined, overBudgetOnly);
  const data = query.data;

  const rows = useMemo(
    () =>
      (data?.items ?? []).map((row) => {
        const snap = row.profit_snapshot;
        const variance = snap.cost_variance;
        const varianceNum = variance != null ? Number(variance) : null;
        const varianceTone =
          varianceNum == null ? "text-zinc-400" : varianceNum > 0 ? "text-red-400" : "text-emerald-400";
        const stage = row.stage ?? "lead";
        return {
          id: row.id,
          projectNo: row.project_no,
          name: row.name,
          stageLabel: STAGE_LABEL[stage] ?? stage,
          ownerName: row.owner_name ?? "",
          budgetCost: money(snap.budget_cost),
          actualCost: money(snap.actual_cost_total),
          variance: money(variance),
          varianceTone,
          realizedProfit: money(snap.realized_profit),
          budgetStatus: snap.budget_status,
          budgetStatusLabel:
            snap.budget_status === "over_budget" ? "超预算" : snap.budget_status === "in_budget" ? "正常" : "—",
        };
      }),
    [data?.items],
  );

  const totals = data?.totals;

  return (
    <IndustrialPage gap="md" fill>
      <div>
        <h1 className={typography.pageTitle}>订单利润</h1>
        <p className="text-xs text-zinc-500">
          跨项目汇总预算成本、实际成本、偏差与毛利。明细登记请前往
          <Link href="/projects" className="mx-1 text-blue-400 hover:underline">
            项目台账
          </Link>
          编辑具体项目。
        </p>
      </div>

      {totals ? (
        <IndustrialPanel title="本页合计">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <KpiCard label="预算成本合计" value={money(totals.budget_cost_total)} />
            <KpiCard label="实际成本合计" value={money(totals.actual_cost_total)} />
            <KpiCard
              label="偏差合计"
              value={money(totals.variance_total)}
              tone={
                totals.variance_total != null && Number(totals.variance_total) > 0
                  ? "text-red-400"
                  : totals.variance_total != null
                    ? "text-emerald-400"
                    : undefined
              }
            />
            <KpiCard label="实际毛利合计" value={money(totals.realized_profit_total)} />
            <KpiCard label="超预算项目" value={String(totals.over_budget_count ?? 0)} tone="text-amber-400" />
          </div>
        </IndustrialPanel>
      ) : null}

      <MasterListPage<LedgerRow>
        embedded
        fill
        title="项目利润台账"
        persistenceKey="order-profit-v1"
        exportFilename="order-profit"
        columns={[
          { key: "projectNo", title: "项目编号", canView: true, fixed: "left", width: 140 },
          { key: "name", title: "项目名称", canView: true, width: 160 },
          { key: "stageLabel", title: "阶段", canView: true, width: 90 },
          { key: "ownerName", title: "负责人", canView: true, width: 90 },
          { key: "budgetCost", title: "预算成本", canView: true, width: 110 },
          { key: "actualCost", title: "实际成本", canView: true, width: 110 },
          { key: "variance", title: "偏差", canView: true, width: 100 },
          { key: "realizedProfit", title: "实际毛利", canView: true, width: 110 },
          { key: "budgetStatusLabel", title: "状态", canView: true, width: 80 },
        ]}
        rows={rows}
        total={data?.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        toolbarExtra={
          <WorkspaceToolbarButton
            onClick={() => {
              setOverBudgetOnly((v) => !v);
              setPage(1);
            }}
          >
            {overBudgetOnly ? "显示全部" : "仅超预算"}
          </WorkspaceToolbarButton>
        }
        emptyHint="暂无项目或尚无成本数据；请先在项目台账创建项目并关联报价与成本核算"
      />
    </IndustrialPage>
  );
}
