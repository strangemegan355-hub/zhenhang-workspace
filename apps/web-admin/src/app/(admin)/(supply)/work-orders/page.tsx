"use client";

import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import {
  useAdvanceWorkOrderMutation,
  useClaimWorkOrderMutation,
  useCreateWorkOrderMutation,
  useDeleteWorkOrderMutation,
  useGenerateWorkOrderChainMutation,
  useMachinesQuery,
  useProjectsQuery,
  useWorkOrderSummaryQuery,
  useWorkOrdersQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, KpiCard, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import {
  fieldInputClass,
  fieldLabelClass,
  inlineBtnClass,
  linkActionClass,
} from "@/lib/form-styles";

type WorkOrderRow = {
  id: string;
  workOrderNo: string;
  projectLabel: string;
  taskDesc: string;
  processLabel: string;
  team: string;
  ownerName: string;
  status: string;
  statusLabel: string;
  planEnd: string;
  claimedBy: string;
};

const PROCESS_OPTIONS = [
  { value: "cutting", label: "下料" },
  { value: "welding", label: "焊装" },
  { value: "assembly", label: "装配" },
  { value: "debug", label: "调试" },
  { value: "shipment", label: "发货" },
];

const defaultForm = {
  project_id: "",
  machine_id: "",
  task_desc: "",
  process_node: "assembly",
  team: "",
  owner_name: "",
  plan_start: "",
  plan_end: "",
  remark: "",
};

export default function WorkOrdersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [chainMsg, setChainMsg] = useState<string | null>(null);
  const [chainProjectId, setChainProjectId] = useState("");

  const query = useWorkOrdersQuery(page, search.trim() || undefined);
  const summaryQuery = useWorkOrderSummaryQuery();
  const projectsQuery = useProjectsQuery(1);
  const machinesQuery = useMachinesQuery(1);
  const createMutation = useCreateWorkOrderMutation();
  const advanceMutation = useAdvanceWorkOrderMutation();
  const claimMutation = useClaimWorkOrderMutation();
  const deleteMutation = useDeleteWorkOrderMutation();
  const chainMutation = useGenerateWorkOrderChainMutation();

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const summary = summaryQuery.data;

  const projectMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of (projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []) {
      map.set(String(p.id ?? ""), `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`);
    }
    return map;
  }, [projectsQuery.data]);

  const projectOptions = useMemo(
    () =>
      ((projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`,
      })),
    [projectsQuery.data],
  );

  const machineOptions = useMemo(
    () =>
      ((machinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.code ?? m.machine_code ?? "")} · ${String(m.name ?? "")}`,
      })),
    [machinesQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => {
        const projectId = String(row.project_id ?? "");
        return {
          id: String(row.id ?? ""),
          workOrderNo: String(row.work_order_no ?? ""),
          projectLabel: projectMap.get(projectId) ?? projectId.slice(0, 8) + "…",
          taskDesc: String(row.task_desc ?? ""),
          processLabel: String(row.process_node_label ?? row.process_node ?? ""),
          team: String(row.team ?? "—"),
          ownerName: String(row.owner_name ?? "—"),
          status: String(row.status ?? "todo"),
          statusLabel: String(row.status_label ?? row.status ?? ""),
          planEnd: row.plan_end ? String(row.plan_end) : "—",
          claimedBy: String(row.claimed_by ?? "—"),
        };
      }),
    [data.items, projectMap],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.project_id || !form.task_desc.trim()) {
      setFormError("请选择项目并填写任务描述");
      return;
    }
    try {
      await createMutation.mutateAsync({
        project_id: form.project_id,
        machine_id: form.machine_id || undefined,
        task_desc: form.task_desc.trim(),
        process_node: form.process_node,
        team: form.team.trim() || undefined,
        owner_name: form.owner_name.trim() || undefined,
        plan_start: form.plan_start || undefined,
        plan_end: form.plan_end || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
      void summaryQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleGenerateChain = async () => {
    setChainMsg(null);
    const projectId = chainProjectId || form.project_id;
    if (!projectId) {
      setChainMsg("请先选择项目");
      return;
    }
    try {
      const result = await chainMutation.mutateAsync({ project_id: projectId, step_days: 3 });
      setChainMsg(`已生成 ${result.created_count} 张标准工序工单`);
      void query.refetch();
      void summaryQuery.refetch();
    } catch (err) {
      setChainMsg(err instanceof Error ? err.message : "生成失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard title="工单总数" value={String(summary?.total ?? 0)} trend="张" />
        <KpiCard title="待认领" value={String(summary?.todo ?? 0)} trend="张" />
        <KpiCard title="进行中" value={String(summary?.doing ?? 0)} trend="张" />
        <KpiCard title="今日完工" value={String(summary?.completed_today ?? 0)} trend="张" />
      </div>

      <IndustrialPanel
        title="标准工序链"
        toolbar={
          <WorkspaceToolbarButton onClick={() => void handleGenerateChain()} disabled={chainMutation.isPending}>
            一键生成五道工序
          </WorkspaceToolbarButton>
        }
      >
        <div className="flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>关联项目</span>
              <select
                className={`${fieldInputClass} min-w-[220px]`}
                value={chainProjectId}
                onChange={(e) => setChainProjectId(e.target.value)}
              >
              <option value="">请选择</option>
              {projectOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          {chainMsg ? <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>{chainMsg}</p> : null}
        </div>
      </IndustrialPanel>

      {showCreate ? (
        <MasterCreateForm
          title="发布工单"
          fields={[
            { key: "project_id", label: "关联项目", required: true, type: "select", options: projectOptions },
            {
              key: "machine_id",
              label: "关联机器",
              type: "select",
              options: [{ value: "", label: "（可选）" }, ...machineOptions],
            },
            { key: "task_desc", label: "任务描述", required: true, placeholder: "如 按图纸装配主机架" },
            { key: "process_node", label: "工序", type: "select", options: PROCESS_OPTIONS },
            { key: "team", label: "班组", placeholder: "如 装配班组" },
            { key: "owner_name", label: "负责人", placeholder: "留空则全员可认领" },
            { key: "plan_start", label: "计划开始", placeholder: "YYYY-MM-DD" },
            { key: "plan_end", label: "计划结束", placeholder: "YYYY-MM-DD" },
            { key: "remark", label: "备注", placeholder: "可选" },
          ]}
          values={form}
          onChange={(key, value) => {
            setForm((s) => {
              const next = { ...s, [key]: value };
              if (key === "machine_id" && value && !s.task_desc.trim()) {
                const machine = machineOptions.find((m) => m.value === value);
                if (machine) next.task_desc = `按图纸加工/装配：${machine.label.split(" · ").pop() ?? ""}`;
              }
              if (key === "project_id") setChainProjectId(String(value));
              return next;
            });
          }}
          onSubmit={() => void handleCreate()}
          onCancel={() => {
            setShowCreate(false);
            setFormError(null);
          }}
          submitting={createMutation.isPending}
          error={formError}
          submitLabel="发布工单"
        />
      ) : null}

      <MasterListPage<WorkOrderRow>
        embedded
        title="车间工单"
        persistenceKey="work-orders-v1"
        exportFilename="work-orders"
        columns={[
          { key: "workOrderNo", title: "工单号", canView: true, fixed: "left", width: 130 },
          { key: "projectLabel", title: "项目", canView: true, width: 140 },
          { key: "taskDesc", title: "任务", canView: true, width: 180 },
          { key: "processLabel", title: "工序", canView: true, width: 70 },
          { key: "team", title: "班组", canView: true, width: 90 },
          { key: "statusLabel", title: "状态", canView: true, width: 80 },
          { key: "claimedBy", title: "认领人", canView: true, width: 80 },
          { key: "planEnd", title: "计划结束", canView: true, width: 100 },
        ]}
        rows={rows}
        total={data.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex gap-1">
            {row.status === "todo" ? (
              <button
                type="button"
                className={linkActionClass}
                disabled={claimMutation.isPending}
                onClick={() =>
                  void claimMutation
                    .mutateAsync({ id: row.id, claimed_by: "车间操作员" })
                    .then(() => query.refetch())
                }
              >
                认领
              </button>
            ) : null}
            {row.status !== "done" ? (
              <button
                type="button"
                className={`${inlineBtnClass} text-[var(--color-success)]`}
                disabled={advanceMutation.isPending}
                onClick={() => void advanceMutation.mutateAsync(row.id).then(() => query.refetch())}
              >
                推进
              </button>
            ) : null}
            {row.status !== "done" ? (
              <button
                type="button"
                className="rounded border border-[#fde8e8] px-2 py-0.5 text-[11px] text-[#ef4444] hover:bg-[#fde8e8] transition-colors dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
                disabled={deleteMutation.isPending}
                onClick={() => void deleteMutation.mutateAsync(row.id).then(() => query.refetch())}
              >
                删除
              </button>
            ) : null}
          </div>
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>发布工单</WorkspaceToolbarButton>}
      />
    </IndustrialPage>
  );
}
