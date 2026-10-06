"use client";

import { useToastStore } from "@zhenhang/realtime";

import {
  useCreateProjectMutation,
  useCustomersQuery,
  useDeleteProjectMutation,
  useProjectSummaryQuery,
  useProjectsQuery,
  useUpdateProjectMutation,
  type ProjectSummary,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { ProjectActualCostsPanel } from "@/components/projects/project-actual-costs-panel";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  dangerActionClass,
  kpiCardClass,
  kpiCardLabelClass,
  kpiCardValueClass,
  linkActionClass,
} from "@/lib/form-styles";

type ProjectRow = {
  id: string;
  projectNo: string;
  name: string;
  stage: string;
  stageLabel: string;
  ownerName: string;
  category: string;
  customerId: string;
  targetDate: string;
  remark: string;
};

const STAGE_OPTIONS = [
  { value: "lead", label: "线索" },
  { value: "quoted", label: "已报价" },
  { value: "ordered", label: "已下单" },
  { value: "manufacturing", label: "生产中" },
  { value: "delivery", label: "待交付" },
  { value: "done", label: "已完成" },
];

const STAGE_LABEL: Record<string, string> = Object.fromEntries(STAGE_OPTIONS.map((o) => [o.value, o.label]));

const emptyForm = {
  name: "",
  customer_id: "",
  category: "",
  stage: "lead",
  owner_name: "",
  target_date: "",
  remark: "",
};

function RowActions({ onEdit, onDelete }: { onEdit: () => void; onDelete: () => void }) {
  return (
    <div className="flex items-center gap-2">
      <button type="button" className={linkActionClass} onClick={onEdit}>
        修改
      </button>
      <button type="button" className={dangerActionClass} onClick={onDelete}>
        删除
      </button>
    </div>
  );
}

function money(n: unknown) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const LINK_STATUS_HINT: Record<string, string> = {
  complete: "",
  missing_quote: "尚未关联对客报价，无法计算收入侧。",
  missing_cost: "尚未关联成本核算，无法计算预算成本。",
  both_missing: "请在对客报价与成本核算中关联本项目后再查看盈亏。",
};

const HEALTH_TONE: Record<string, string> = {
  good: "text-[var(--color-success)]",
  warn: "text-[var(--color-warning)]",
  bad: "text-[var(--color-danger)]",
  unknown: "text-[var(--color-text-muted)]",
};

const VARIANCE_TONE: Record<string, string> = {
  in_budget: "text-[var(--color-success)]",
  over_budget: "text-[var(--color-danger)]",
  unknown: "text-[var(--color-text-muted)]",
};

function KpiCard({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className={kpiCardClass}>
      <div className={kpiCardLabelClass}>{label}</div>
      <div className={`${kpiCardValueClass} ${tone ?? ""}`}>{value}</div>
    </div>
  );
}

export default function ProjectsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [editId, setEditId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useProjectsQuery(page, search.trim() || undefined);
  const customersQuery = useCustomersQuery(1);
  const summaryQuery = useProjectSummaryQuery(editId ?? undefined);
  const createMutation = useCreateProjectMutation();
  const updateMutation = useUpdateProjectMutation();
  const deleteMutation = useDeleteProjectMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const customerOptions = useMemo(
    () =>
      ((customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c) => ({
        value: String(c.id ?? ""),
        label: `${String(c.code ?? "")} · ${String(c.name ?? "")}`,
      })),
    [customersQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => {
        const stage = String(row.stage ?? "lead");
        return {
          id: String(row.id ?? ""),
          projectNo: String(row.project_no ?? ""),
          name: String(row.name ?? ""),
          stage,
          stageLabel: STAGE_LABEL[stage] ?? stage,
          ownerName: String(row.owner_name ?? ""),
          category: String(row.category ?? ""),
          customerId: String(row.customer_id ?? ""),
          targetDate: String(row.target_date ?? ""),
          remark: String(row.remark ?? ""),
        };
      }),
    [data.items],
  );

  const closeForm = () => {
    setShowForm(false);
    setEditId(null);
    setForm(emptyForm);
    setFormError(null);
  };

  const openCreate = () => {
    closeForm();
    setShowForm(true);
  };

  const openEdit = (row: ProjectRow) => {
    setEditId(row.id);
    setForm({
      name: row.name,
      customer_id: row.customerId,
      category: row.category,
      stage: row.stage,
      owner_name: row.ownerName,
      target_date: row.targetDate ? row.targetDate.slice(0, 10) : "",
      remark: row.remark,
    });
    setShowForm(true);
    setFormError(null);
  };

  const summary = summaryQuery.data as ProjectSummary | undefined;
  const linkedQuote = summary?.linked_quote;
  const linkedCost = summary?.linked_cost_estimate;
  const profit = summary?.profit_snapshot;
  const linkHint = profit ? LINK_STATUS_HINT[profit.link_status] ?? "" : "";
  const marginTone = profit ? HEALTH_TONE[profit.health] ?? HEALTH_TONE.unknown : HEALTH_TONE.unknown;
  const varianceTone = profit ? VARIANCE_TONE[profit.budget_status] ?? VARIANCE_TONE.unknown : HEALTH_TONE.unknown;
  const realizedTone =
    profit?.realized_margin_pct != null
      ? HEALTH_TONE[
          Number(profit.realized_margin_pct) < 8 ? "bad" : Number(profit.realized_margin_pct) < 15 ? "warn" : "good"
        ]
      : HEALTH_TONE.unknown;

  const handleSave = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写项目名称");
      return;
    }
    const body = {
      name: form.name.trim(),
      customer_id: form.customer_id.trim() || undefined,
      category: form.category.trim() || undefined,
      stage: form.stage || "lead",
      owner_name: form.owner_name.trim() || undefined,
      target_date: form.target_date || undefined,
      remark: form.remark.trim() || undefined,
    };
    try {
      if (editId) await updateMutation.mutateAsync({ id: editId, body });
      else await createMutation.mutateAsync(body);
      closeForm();
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`确认删除项目「${label}」？`)) return;
    try {
      await deleteMutation.mutateAsync(id);
      if (editId === id) closeForm();
      void query.refetch();
    } catch (err) {
      notify(err instanceof Error ? err.message : "删除失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="项目台账"
        subtitle="项目主数据统一接入页面标题与页面壳层"
        actions={<WorkspaceToolbarButton onClick={openCreate}>新增项目</WorkspaceToolbarButton>}
      />

      {showForm ? (
        <MasterCreateForm
          title={editId ? "修改项目" : "新增项目"}
          fields={[
            { key: "name", label: "项目名称", required: true, placeholder: "如 XX客户设备项目" },
            { key: "customer_id", label: "客户", type: "select", options: customerOptions },
            { key: "category", label: "产品分类", placeholder: "如 注塑机/压铸机" },
            { key: "stage", label: "阶段", type: "select", options: STAGE_OPTIONS },
            { key: "owner_name", label: "负责人", placeholder: "项目负责人姓名" },
            { key: "target_date", label: "目标交付日", type: "text", placeholder: "YYYY-MM-DD" },
            { key: "remark", label: "备注" },
          ]}
          values={form}
          onChange={(key, value) => setForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSave()}
          onCancel={closeForm}
          submitting={createMutation.isPending || updateMutation.isPending}
          error={formError}
          submitLabel={editId ? "保存修改" : "保存"}
        />
      ) : null}

      {editId && showForm && summary ? (
        <IndustrialPanel title="项目盈亏与关联">
          {linkHint ? <p className="mb-3 text-xs text-amber-400">{linkHint}</p> : null}
          {profit ? (
            <>
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <KpiCard label="税前收入（对客报价）" value={profit.revenue_before_tax != null ? money(profit.revenue_before_tax) : "—"} />
                <KpiCard label="预算成本（完全成本）" value={profit.budget_cost != null ? money(profit.budget_cost) : "—"} />
                <KpiCard label="预算毛利" value={profit.expected_profit != null ? money(profit.expected_profit) : "—"} tone={profit.expected_profit != null ? marginTone : undefined} />
                <KpiCard label="预算利润率" value={profit.profit_margin_pct != null ? `${money(profit.profit_margin_pct)}%` : "—"} tone={profit.profit_margin_pct != null ? marginTone : undefined} />
              </div>
              <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <KpiCard label="实际成本" value={profit.actual_cost_total != null ? money(profit.actual_cost_total) : "—"} />
                <KpiCard label="预算偏差" value={profit.cost_variance != null ? money(profit.cost_variance) : "—"} tone={profit.cost_variance != null ? varianceTone : undefined} />
                <KpiCard label="实际毛利" value={profit.realized_profit != null ? money(profit.realized_profit) : "—"} tone={profit.realized_profit != null ? realizedTone : undefined} />
                <KpiCard label="实际利润率" value={profit.realized_margin_pct != null ? `${money(profit.realized_margin_pct)}%` : "—"} tone={profit.realized_margin_pct != null ? realizedTone : undefined} />
              </div>
            </>
          ) : null}
          <div className="grid gap-2 text-xs md:grid-cols-2 lg:grid-cols-4">
            <div>关联报价数：{String(summary.quote_count ?? 0)}</div>
            <div>成本核算数：{String(summary.cost_estimate_count ?? 0)}</div>
            <div>实际成本登记：{String(summary.actual_cost_count ?? 0)}</div>
            {linkedQuote ? (
              <div className="md:col-span-2">
                关联报价：
                <Link href="/quotes/customer" className="ml-1 text-blue-400 hover:underline">
                  {linkedQuote.quote_no} · {linkedQuote.title}（含税 {money(linkedQuote.total_amount)}）
                </Link>
              </div>
            ) : (
              <div className="text-zinc-500 md:col-span-2">尚未关联报价，可在对客报价中选择本项目</div>
            )}
            {linkedCost ? (
              <div className="md:col-span-2">
                关联成本核算：{linkedCost.estimate_no} · {linkedCost.product_name}（完全成本 {money(linkedCost.total_cost)}）
              </div>
            ) : null}
          </div>
          <p className="mt-2 text-[11px] text-zinc-500">
            预算侧取自对客报价与成本核算完全成本；实际侧来自下方登记。偏差 = 实际成本 − 预算成本，正数为超预算。
          </p>
        </IndustrialPanel>
      ) : null}

      {editId && showForm ? <ProjectActualCostsPanel projectId={editId} /> : null}

      <MasterListPage<ProjectRow>
        hideInternalHeader
        pageShellMode="embedded"
        embedded
        fill
        title="项目台账"
        persistenceKey="projects-v1"
        exportFilename="projects"
        columns={[
          { key: "projectNo", title: "项目编号", canView: true, fixed: "left", width: 150 },
          { key: "name", title: "项目名称", canView: true, width: 180 },
          { key: "stageLabel", title: "阶段", canView: true, width: 90 },
          { key: "ownerName", title: "负责人", canView: true, width: 100 },
          { key: "category", title: "分类", canView: true },
        ]}
        rows={rows}
        total={data.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        rowActions={(row) => <RowActions onEdit={() => openEdit(row)} onDelete={() => void handleDelete(row.id, row.name)} />}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreate}>新增项目</WorkspaceToolbarButton>}
        emptyHint="项目台账用于汇总预算与报价；创建后可在对客报价、成本核算中关联本项目"
      />
    </IndustrialPage>
  );
}

function notify(title: string) {
  useToastStore.getState().push({ title });
}
