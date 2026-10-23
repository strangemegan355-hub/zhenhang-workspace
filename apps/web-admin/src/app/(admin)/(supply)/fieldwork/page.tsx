"use client";

import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { inlineBtnClass, inlineBtnDangerClass } from "@/lib/form-styles";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";
import {
  useAdvanceFieldworkStatusMutation,
  useCreateFieldworkRecordMutation,
  useCustomersQuery,
  useDeleteFieldworkRecordMutation,
  useFieldworkRecordsQuery,
  useFieldworkSummaryQuery,
  useMachinesQuery,
  useMaterialsQuery,
  usePostFieldworkReceivableMutation,
  useProjectsQuery,
  useUpdateFieldworkRecordMutation,
  useAftersalesQuery,
  type FieldworkRecordPayload,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, KpiCard, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";

type FieldworkRow = {
  id: string;
  recordNo: string;
  typeLabel: string;
  headline: string;
  statusLabel: string;
  reporter: string;
  occurredOn: string;
  status: string;
  recordType: string;
  repairAmount: string;
  receivableEntryId: string;
  receivableLabel: string;
};

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

type TabKey = "repair" | "shortage" | "loading" | "all";

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: "repair", label: "外出维修", icon: "🔧" },
  { key: "shortage", label: "缺料上报", icon: "📦" },
  { key: "loading", label: "装车登记", icon: "🚛" },
  { key: "all", label: "全部记录", icon: "📋" },
];

const repairDefaults = {
  customer_id: "",
  occurred_on: new Date().toISOString().slice(0, 10),
  headline: "",
  detail: "",
  hours: "1",
  repair_amount: "",
  remark: "",
  service_request_id: "",
};

const shortageDefaults = {
  machine_id: "",
  project_id: "",
  material_id: "",
  headline: "",
  detail: "",
  qty: "1",
  urgency: "normal",
  remark: "",
};

const loadingDefaults = {
  customer_id: "",
  occurred_on: new Date().toISOString().slice(0, 10),
  headline: "",
  detail: "",
  remark: "",
  transport_type: "truck",
};

export default function FieldworkPage() {
  const user = useAuthStore((s) => s.user);
  const perms = user?.permissions ?? [];
  const canPostReceivable = hasPermission(perms, "business:accounting:create");

  const [tab, setTab] = useState<TabKey>("repair");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [repairForm, setRepairForm] = useState(repairDefaults);
  const [shortageForm, setShortageForm] = useState(shortageDefaults);
  const [loadingForm, setLoadingForm] = useState(loadingDefaults);

  const recordType = tab === "all" ? undefined : tab;
  const query = useFieldworkRecordsQuery(page, search.trim() || undefined, recordType);
  const summaryQuery = useFieldworkSummaryQuery();
  const customersQuery = useCustomersQuery(1);
  const machinesQuery = useMachinesQuery(1);
  const materialsQuery = useMaterialsQuery(1);
  const projectsQuery = useProjectsQuery(1);
  const createMutation = useCreateFieldworkRecordMutation();
  const advanceMutation = useAdvanceFieldworkStatusMutation();
  const deleteMutation = useDeleteFieldworkRecordMutation();
  const updateMutation = useUpdateFieldworkRecordMutation();
  const postReceivableMutation = usePostFieldworkReceivableMutation();
  const aftersalesQuery = useAftersalesQuery(1, { status: "confirmed" });

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const summary = summaryQuery.data;

  const customerOptions = useMemo(
    () =>
      ((customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c) => ({
        value: String(c.id ?? ""),
        label: String(c.name ?? c.company_name ?? ""),
      })),
    [customersQuery.data],
  );

  const machineOptions = useMemo(
    () =>
      ((machinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.code ?? m.machine_code ?? "")} · ${String(m.name ?? "")}`,
      })),
    [machinesQuery.data],
  );

  const materialOptions = useMemo(
    () =>
      ((materialsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.code ?? "")} · ${String(m.name ?? "")}`,
        spec: String(m.spec ?? ""),
      })),
    [materialsQuery.data],
  );

  const aftersalesOptions = useMemo(
    () => [
      { value: "", label: "（不关联）" },
      ...((aftersalesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((a) => ({
        value: String(a.id ?? ""),
        label: `${String(a.request_no ?? "")} ${String(a.title ?? "")}`,
      })),
    ],
    [aftersalesQuery.data],
  );

  const projectOptions = useMemo(
    () =>
      ((projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`,
      })),
    [projectsQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        recordNo: String(row.record_no ?? ""),
        typeLabel: String(row.record_type_label ?? row.record_type ?? ""),
        headline: String(row.headline ?? ""),
        statusLabel: String(row.status_label ?? row.status ?? ""),
        reporter: String(row.reporter_name ?? "—"),
        occurredOn: row.occurred_on ? String(row.occurred_on) : "—",
        status: String(row.status ?? ""),
        recordType: String(row.record_type ?? ""),
        repairAmount: row.repair_amount != null ? money(row.repair_amount as number | string) : "—",
        receivableEntryId: String(row.receivable_entry_id ?? ""),
        receivableLabel:
          String(row.record_type ?? "") === "repair"
            ? row.receivable_entry_id
              ? "已生成"
              : "未生成"
            : "—",
        serviceRequestId: String(row.service_request_id ?? ""),
        serviceRequestTitle: String(row.service_request_title ?? ""),
      })),
    [data.items],
  );

  const submit = async (payload: FieldworkRecordPayload) => {
    setFormError(null);
    try {
      await createMutation.mutateAsync(payload);
      void query.refetch();
      void summaryQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "提交失败");
    }
  };

  const handleRepairSubmit = () => {
    if (!repairForm.customer_id || !repairForm.headline.trim()) {
      setFormError("请选择客户并填写故障描述");
      return;
    }
    void submit({
      record_type: "repair",
      customer_id: repairForm.customer_id,
      occurred_on: repairForm.occurred_on,
      headline: repairForm.headline.trim(),
      detail: repairForm.detail.trim() || undefined,
      hours: Number(repairForm.hours || 0),
      repair_amount: repairForm.repair_amount ? Number(repairForm.repair_amount) : undefined,
      remark: repairForm.remark.trim() || undefined,
      service_request_id: repairForm.service_request_id || undefined,
    }).then(() => setRepairForm(repairDefaults));
  };

  const handleShortageSubmit = () => {
    if (!shortageForm.machine_id || !shortageForm.material_id) {
      setFormError("请选择机器和物料");
      return;
    }
    const mat = materialOptions.find((m) => m.value === shortageForm.material_id);
    void submit({
      record_type: "shortage",
      machine_id: shortageForm.machine_id,
      project_id: shortageForm.project_id || undefined,
      material_id: shortageForm.material_id,
      headline: shortageForm.headline.trim() || mat?.label || "缺料上报",
      detail: shortageForm.detail.trim() || mat?.spec || undefined,
      qty: Number(shortageForm.qty || 1),
      urgency: shortageForm.urgency,
      remark: shortageForm.remark.trim() || undefined,
    }).then(() => setShortageForm(shortageDefaults));
  };

  const handleLoadingSubmit = () => {
    if (!loadingForm.customer_id || !loadingForm.headline.trim()) {
      setFormError("请选择客户并填写货物描述");
      return;
    }
    void submit({
      record_type: "loading",
      customer_id: loadingForm.customer_id,
      occurred_on: loadingForm.occurred_on,
      headline: loadingForm.headline.trim(),
      detail: loadingForm.detail.trim() || undefined,
      extra: { transport_type: loadingForm.transport_type },
      remark: loadingForm.remark.trim() || undefined,
    }).then(() => setLoadingForm(loadingDefaults));
  };

  return (
    <IndustrialPage gap="md" fill>
      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard title="维修记录" value={String(summary?.repair ?? 0)} trend="条" />
        <KpiCard title="缺料上报" value={String(summary?.shortage ?? 0)} trend="条" />
        <KpiCard title="装车登记" value={String(summary?.loading ?? 0)} trend="条" />
        <KpiCard title="待处理缺料" value={String(summary?.open_shortages ?? 0)} trend="条" />
      </div>

      <IndustrialPanel title="作业类型">
        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <WorkspaceToolbarButton key={t.key} onClick={() => { setTab(t.key); setPage(1); }}>
              {t.icon} {t.label}
            </WorkspaceToolbarButton>
          ))}
        </div>
      </IndustrialPanel>

      {tab === "repair" ? (
        <MasterCreateForm
          title="外出维修登记"
          fields={[
            { key: "customer_id", label: "客户", required: true, type: "select", options: customerOptions },
            { key: "occurred_on", label: "维修日期", type: "date" },
            { key: "headline", label: "故障描述", required: true, placeholder: "设备出现了什么问题" },
            { key: "detail", label: "处理措施", placeholder: "怎么修的" },
            { key: "hours", label: "工时(小时)", type: "number" },
            { key: "repair_amount", label: "维修费用(元)", type: "number", placeholder: "可稍后填写" },
            { key: "remark", label: "备注", placeholder: "其他说明" },
            { key: "service_request_id", label: "关联工单", type: "select", options: aftersalesOptions },
          ]}
          values={{ ...repairForm, service_request_id: repairForm.service_request_id || "" }}
          onChange={(key, value) => setRepairForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleRepairSubmit()}
          onCancel={() => setRepairForm(repairDefaults)}
          submitting={createMutation.isPending}
          error={formError}
          submitLabel="提交维修记录"
        />
      ) : null}

      {tab === "shortage" ? (
        <MasterCreateForm
          title="缺料上报"
          fields={[
            { key: "machine_id", label: "机器", required: true, type: "select", options: machineOptions },
            {
              key: "project_id",
              label: "关联项目",
              type: "select",
              options: [{ value: "", label: "（可选）" }, ...projectOptions],
            },
            { key: "material_id", label: "物料", required: true, type: "select", options: materialOptions },
            { key: "qty", label: "需要数量", type: "number" },
            {
              key: "urgency",
              label: "紧急程度",
              type: "select",
              options: [
                { value: "normal", label: "正常" },
                { value: "urgent", label: "紧急" },
                { value: "critical", label: "非常紧急" },
              ],
            },
            { key: "headline", label: "说明", placeholder: "可选，默认取物料名" },
            { key: "remark", label: "备注", placeholder: "补充说明" },
          ]}
          values={shortageForm}
          onChange={(key, value) => {
            setShortageForm((s) => {
              const next = { ...s, [key]: value };
              if (key === "material_id") {
                const mat = materialOptions.find((m) => m.value === value);
                if (mat && !s.headline) next.headline = mat.label.split(" · ").pop() ?? "";
                if (mat) next.detail = mat.spec;
              }
              return next;
            });
          }}
          onSubmit={() => void handleShortageSubmit()}
          onCancel={() => setShortageForm(shortageDefaults)}
          submitting={createMutation.isPending}
          error={formError}
          submitLabel="提交缺料申请"
        />
      ) : null}

      {tab === "loading" ? (
        <MasterCreateForm
          title="装车登记"
          fields={[
            { key: "customer_id", label: "客户", required: true, type: "select", options: customerOptions },
            { key: "occurred_on", label: "装车日期", type: "date" },
            { key: "headline", label: "货物描述", required: true, placeholder: "装车内容摘要" },
            { key: "detail", label: "设备明细", placeholder: "如 XX机型 × 1" },
            {
              key: "transport_type",
              label: "运输方式",
              type: "select",
              options: [
                { value: "truck", label: "货车" },
                { value: "logistics", label: "物流" },
                { value: "self", label: "自提" },
              ],
            },
            { key: "remark", label: "备注", placeholder: "可选" },
          ]}
          values={loadingForm}
          onChange={(key, value) => setLoadingForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleLoadingSubmit()}
          onCancel={() => setLoadingForm(loadingDefaults)}
          submitting={createMutation.isPending}
          error={formError}
          submitLabel="提交装车记录"
        />
      ) : null}

      {formError ? (
        <IndustrialPanel>
          <p className="text-xs text-[var(--color-danger)]">{formError}</p>
        </IndustrialPanel>
      ) : null}

      <MasterListPage<FieldworkRow>
        embedded
        title={tab === "all" ? "全部现场作业" : TABS.find((t) => t.key === tab)?.label ?? "现场作业"}
        persistenceKey={`fieldwork-${tab}-v1`}
        exportFilename={`fieldwork-${tab}`}
        columns={[
          { key: "recordNo", title: "单号", canView: true, fixed: "left", width: 130 },
          ...(tab === "all" ? [{ key: "typeLabel" as const, title: "类型", canView: true, width: 90 }] : []),
          { key: "headline", title: "摘要", canView: true, width: 200 },
          ...(tab === "repair" || tab === "all"
            ? [
                { key: "repairAmount" as const, title: "维修费", canView: true, width: 90 },
                { key: "receivableLabel" as const, title: "应收", canView: true, width: 80 },
              ]
            : []),
          { key: "reporter", title: "上报人", canView: true, width: 90 },
          { key: "occurredOn", title: "日期", canView: true, width: 100 },
          { key: "statusLabel", title: "状态", canView: true, width: 80 },
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
          <div className="flex flex-wrap gap-1">
            {row.recordType === "repair" && canPostReceivable && !row.receivableEntryId ? (
              row.repairAmount === "—" ? (
                <button
                  type="button"
                  className={inlineBtnClass}
                  disabled={updateMutation.isPending}
                  onClick={() => {
                    const v = window.prompt("请输入维修费用（元）");
                    if (!v || Number(v) <= 0) return;
                    void updateMutation
                      .mutateAsync({ id: row.id, body: { repair_amount: Number(v) } })
                      .then(() => query.refetch());
                  }}
                >
                  填费用
                </button>
              ) : (
                <button
                  type="button"
                  className={inlineBtnClass}
                  disabled={postReceivableMutation.isPending}
                  onClick={() =>
                    void postReceivableMutation.mutateAsync(row.id).then(() => {
                      void query.refetch();
                      setFormError(null);
                    }).catch((err) => setFormError(err instanceof Error ? err.message : "生成应收失败"))
                  }
                >
                  生成应收
                </button>
              )
            ) : null}
            {row.status !== "closed" ? (
              <button
                type="button"
                className={inlineBtnClass}
                disabled={advanceMutation.isPending}
                onClick={() => void advanceMutation.mutateAsync(row.id).then(() => query.refetch())}
              >
                推进
              </button>
            ) : null}
            <button
              type="button"
              className={inlineBtnDangerClass}
              disabled={deleteMutation.isPending}
              onClick={() => void deleteMutation.mutateAsync(row.id).then(() => query.refetch())}
            >
              删除
            </button>
          </div>
        )}
      />
    </IndustrialPage>
  );
}
