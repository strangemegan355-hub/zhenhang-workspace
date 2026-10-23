"use client";

import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { inlineBtnClass, inlineBtnDangerClass, linkActionClass, messageBannerClass } from "@/lib/form-styles";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";
import {
  useAccountingStatusQuery,
  useAdvanceProcurementStatusMutation,
  useCreateProcurementEntryMutation,
  useCreateProcurementPayableRequestMutation,
  useDeleteProcurementEntryMutation,
  useMaterialsQuery,
  useProcurementEntriesQuery,
  useProjectsQuery,
  useSuppliersQuery,
  useTransferProcurementArrivedMutation,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";

type ProcurementRow = {
  id: string;
  requestNo: string;
  projectLabel: string;
  materialId: string;
  supplierId: string;
  qty: string;
  unitPrice: string;
  planAmount: string;
  status: string;
  statusLabel: string;
  transferred: string;
  needDate: string;
  payableStatus: string;
  payableLabel: string;
};

const STATUS_LABELS: Record<string, string> = {
  planned: "计划",
  ordered: "已下单",
  arrived: "已到货",
};

const PAYABLE_LABELS: Record<string, string> = {
  none: "未提交",
  pending: "审批中",
  posted: "已生成应付",
};

const defaultForm = {
  project_id: "",
  material_id: "",
  supplier_id: "",
  qty: "1",
  unit_price: "",
  lead_days: "7",
  need_date: "",
  remark: "",
};

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function ProcurementPage() {
  const user = useAuthStore((s) => s.user);
  const perms = user?.permissions ?? [];
  const canPostPayable = hasPermission(perms, "business:accounting:post_payable");

  const statusQuery = useAccountingStatusQuery();
  const payableEnabled =
    (statusQuery.data?.flags.accounting_enabled ?? false) &&
    (statusQuery.data?.flags.procurement_approval_enabled ?? false);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [transferMsg, setTransferMsg] = useState<string | null>(null);

  const query = useProcurementEntriesQuery(page, search.trim() || undefined);
  const materialsQuery = useMaterialsQuery(1);
  const suppliersQuery = useSuppliersQuery(1);
  const projectsQuery = useProjectsQuery(1);
  const createMutation = useCreateProcurementEntryMutation();
  const advanceMutation = useAdvanceProcurementStatusMutation();
  const deleteMutation = useDeleteProcurementEntryMutation();
  const transferMutation = useTransferProcurementArrivedMutation();
  const postPayableMutation = useCreateProcurementPayableRequestMutation();

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const materialMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const m of (materialsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []) {
      map.set(String(m.id ?? ""), `${String(m.code ?? "")} · ${String(m.name ?? "")}`);
    }
    return map;
  }, [materialsQuery.data]);

  const supplierMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const s of (suppliersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []) {
      map.set(String(s.id ?? ""), String(s.name ?? ""));
    }
    return map;
  }, [suppliersQuery.data]);

  const projectOptions = useMemo(
    () =>
      ((projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`,
      })),
    [projectsQuery.data],
  );

  const materialOptions = useMemo(
    () =>
      ((materialsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.code ?? "")} · ${String(m.name ?? "")}`,
        price: Number(m.reference_price ?? 0),
      })),
    [materialsQuery.data],
  );

  const supplierOptions = useMemo(
    () =>
      ((suppliersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((s) => ({
        value: String(s.id ?? ""),
        label: String(s.name ?? ""),
      })),
    [suppliersQuery.data],
  );

  const projectMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of (projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []) {
      map.set(String(p.id ?? ""), `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`);
    }
    return map;
  }, [projectsQuery.data]);

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => {
        const status = String(row.status ?? "planned");
        const materialId = String(row.material_id ?? "");
        const supplierId = String(row.supplier_id ?? "");
        const projectId = row.project_id ? String(row.project_id) : "";
        const payableStatus = String(row.payable_status ?? "none");
        return {
          id: String(row.id ?? ""),
          requestNo: String(row.request_no ?? ""),
          projectLabel: projectId ? (projectMap.get(projectId) ?? projectId.slice(0, 8) + "…") : "—",
          materialId,
          materialLabel: materialMap.get(materialId) ?? materialId.slice(0, 8),
          supplierId,
          supplierLabel: supplierMap.get(supplierId) ?? supplierId.slice(0, 8),
          qty: String(row.qty ?? ""),
          unitPrice: money(row.unit_price as number | string),
          planAmount: money(row.plan_amount as number | string),
          status,
          statusLabel: STATUS_LABELS[status] ?? status,
          transferred: row.transferred_to_actual ? "已转入" : "—",
          needDate: row.need_date ? String(row.need_date) : "—",
          payableStatus,
          payableLabel: PAYABLE_LABELS[payableStatus] ?? payableStatus,
        };
      }),
    [data.items, materialMap, supplierMap, projectMap],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.material_id || !form.supplier_id || !form.qty || !form.unit_price) {
      setFormError("请填写材料、供应商、数量与单价");
      return;
    }
    try {
      await createMutation.mutateAsync({
        project_id: form.project_id || undefined,
        material_id: form.material_id,
        supplier_id: form.supplier_id,
        qty: Number(form.qty),
        unit_price: Number(form.unit_price),
        lead_days: Number(form.lead_days || 7),
        need_date: form.need_date || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleTransfer = async () => {
    setTransferMsg(null);
    try {
      const result = await transferMutation.mutateAsync();
      setTransferMsg(`已转入 ${result.transferred_count} 条，跳过 ${result.skipped_count} 条`);
      void query.refetch();
    } catch (err) {
      setTransferMsg(err instanceof Error ? err.message : "转入失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="采购预备"
        subtitle="关联项目与材料建请购；推进到货后转实际成本；提交应付后在财务中心跟进，无需重复录入供应商。"
        actions={
          <>
            {payableEnabled ? (
              <Link href="/accounting/supplier-ledger" className="btn-default h-8 px-3 text-xs">
                供应商应付
              </Link>
            ) : null}
            <WorkspaceToolbarButton variant="primary" onClick={() => setShowCreate(true)}>
              新增计划
            </WorkspaceToolbarButton>
          </>
        }
      />

      {showCreate ? (
        <MasterCreateForm
          title="新增采购计划"
          fields={[
            {
              key: "project_id",
              label: "关联项目",
              type: "select",
              options: [{ value: "", label: "（可选）" }, ...projectOptions],
            },
            {
              key: "material_id",
              label: "材料",
              required: true,
              type: "select",
              options: materialOptions.map((o) => ({ value: o.value, label: o.label })),
            },
            {
              key: "supplier_id",
              label: "供应商",
              required: true,
              type: "select",
              options: supplierOptions,
            },
            { key: "qty", label: "数量", required: true, placeholder: "如 10" },
            { key: "unit_price", label: "单价 (CNY)", required: true, placeholder: "如 125.50" },
            { key: "lead_days", label: "交期(天)", placeholder: "默认 7" },
            { key: "need_date", label: "需求日期", type: "date" },
            { key: "remark", label: "备注", placeholder: "用途、规格补充等" },
          ]}
          values={form}
          onChange={(key, value) => {
            setForm((s) => {
              const next = { ...s, [key]: value };
              if (key === "material_id") {
                const mat = materialOptions.find((m) => m.value === value);
                if (mat && mat.price > 0 && !s.unit_price) {
                  next.unit_price = String(mat.price);
                }
              }
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
        />
      ) : null}

      {transferMsg ? <p className={messageBannerClass}>{transferMsg}</p> : null}
      {formError && !showCreate ? <p className={messageBannerClass}>{formError}</p> : null}

      <MasterListPage<ProcurementRow & { materialLabel: string; supplierLabel: string }>
        embedded
        hideInternalHeader
        title="采购预备"
        persistenceKey="procurement-v1"
        exportFilename="procurement"
        columns={[
          { key: "requestNo", title: "请购单号", canView: true, fixed: "left", width: 140 },
          { key: "projectLabel", title: "项目", canView: true, width: 140 },
          { key: "materialLabel", title: "材料", canView: true, width: 160 },
          { key: "supplierLabel", title: "供应商", canView: true, width: 120 },
          { key: "qty", title: "数量", canView: true, width: 70, align: "right" },
          { key: "unitPrice", title: "单价 (CNY)", canView: true, width: 100, align: "right" },
          { key: "planAmount", title: "计划金额 (CNY)", canView: true, width: 120, align: "right" },
          { key: "statusLabel", title: "状态", canView: true, width: 80 },
          ...(payableEnabled
            ? [{ key: "payableLabel" as const, title: "应付", canView: true, width: 90 }]
            : []),
          { key: "transferred", title: "实际成本", canView: true, width: 80 },
          { key: "needDate", title: "需求日", canView: true, width: 100 },
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
            {payableEnabled && canPostPayable && row.payableStatus === "none" && row.status !== "planned" ? (
              <button
                type="button"
                className={inlineBtnClass}
                disabled={postPayableMutation.isPending}
                onClick={() =>
                  void postPayableMutation
                    .mutateAsync(row.id)
                    .then(() => query.refetch())
                    .catch((err) => setFormError(err instanceof Error ? err.message : "提交应付失败"))
                }
              >
                提交应付
              </button>
            ) : null}
            {payableEnabled && (row.payableStatus === "pending" || row.payableStatus === "posted") ? (
              <Link href="/accounting/supplier-ledger" className={linkActionClass}>
                查看应付
              </Link>
            ) : null}
            {row.status !== "arrived" && !row.transferred.startsWith("已") ? (
              <button
                type="button"
                className={inlineBtnClass}
                disabled={advanceMutation.isPending}
                onClick={() => void advanceMutation.mutateAsync(row.id).then(() => query.refetch())}
              >
                推进
              </button>
            ) : null}
            {!row.transferred.startsWith("已") ? (
              <button
                type="button"
                className={inlineBtnDangerClass}
                disabled={deleteMutation.isPending}
                onClick={() => {
                  if (!window.confirm(`确定删除请购单「${row.requestNo}」吗？`)) return;
                  void deleteMutation.mutateAsync(row.id).then(() => query.refetch());
                }}
              >
                删除
              </button>
            ) : null}
          </div>
        )}
        toolbarExtra={
          <WorkspaceToolbarButton
            onClick={() => void handleTransfer()}
            disabled={transferMutation.isPending}
            loading={transferMutation.isPending}
          >
            已到货转实际成本
          </WorkspaceToolbarButton>
        }
        emptyHint="暂无采购计划。点击「新增计划」关联项目与材料；单价可从材料主数据带出。"
      />
    </IndustrialPage>
  );
}
