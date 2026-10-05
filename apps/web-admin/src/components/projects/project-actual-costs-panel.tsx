"use client";

import {
  useCreateProjectActualCostMutation,
  useDeleteProjectActualCostMutation,
  useProjectActualCostsQuery,
  useSuppliersQuery,
} from "@zhenhang/query-hooks";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { IndustrialPanel, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import { tableBodyRowClass, tableHeaderRowClass } from "@/lib/form-styles";

const COST_CATEGORY_OPTIONS = [
  { value: "material", label: "材料与外购件", code: "MAT" },
  { value: "labor", label: "装配与人工", code: "LAB" },
  { value: "outsource", label: "外协运输安装", code: "OUT" },
];

const SOURCE_OPTIONS = [
  { value: "采购", label: "采购" },
  { value: "外协", label: "外协" },
  { value: "运输安装", label: "运输安装" },
  { value: "人工", label: "人工" },
  { value: "其他", label: "其他" },
];

const emptyForm = {
  cost_category: "material",
  amount: "",
  source: "采购",
  supplier_id: "",
  occurred_on: new Date().toISOString().slice(0, 10),
  remark: "",
};

function money(n: unknown) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function categoryLabel(value: string) {
  return COST_CATEGORY_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function ProjectActualCostsPanel({ projectId }: { projectId: string }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);

  const listQuery = useProjectActualCostsQuery(projectId);
  const suppliersQuery = useSuppliersQuery(1);
  const createMutation = useCreateProjectActualCostMutation();
  const deleteMutation = useDeleteProjectActualCostMutation();

  const supplierOptions = useMemo(
    () =>
      ((suppliersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((s) => ({
        value: String(s.id ?? ""),
        label: `${String(s.code ?? "")} · ${String(s.name ?? "")}`,
      })),
    [suppliersQuery.data],
  );

  const rows = useMemo(
    () =>
      ((listQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        costCategory: String(row.cost_category ?? ""),
        costItemName: String(row.cost_item_name ?? ""),
        amount: row.amount,
        source: String(row.source ?? ""),
        occurredOn: String(row.occurred_on ?? "").slice(0, 10),
        remark: String(row.remark ?? ""),
      })),
    [listQuery.data],
  );

  const handleSave = async () => {
    setFormError(null);
    const amount = Number(form.amount);
    if (!amount || amount <= 0) {
      setFormError("请填写大于 0 的金额");
      return;
    }
    if (!form.occurred_on) {
      setFormError("请选择发生日期");
      return;
    }
    const category = COST_CATEGORY_OPTIONS.find((o) => o.value === form.cost_category) ?? COST_CATEGORY_OPTIONS[0];
    try {
      await createMutation.mutateAsync({
        project_id: projectId,
        cost_category: category.value,
        cost_item_code: category.code,
        cost_item_name: category.label,
        amount,
        source: form.source || "采购",
        supplier_id: form.supplier_id.trim() || undefined,
        occurred_on: form.occurred_on,
        remark: form.remark.trim() || undefined,
      });
      setForm(emptyForm);
      setShowForm(false);
      void listQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "登记失败");
    }
  };

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`确认删除实际成本「${label}」？`)) return;
    try {
      await deleteMutation.mutateAsync({ id, projectId });
      void listQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  return (
    <IndustrialPanel
      title="实际成本登记"
      toolbar={
        <WorkspaceToolbarButton onClick={() => setShowForm((v) => !v)}>
          {showForm ? "收起表单" : "登记实际成本"}
        </WorkspaceToolbarButton>
      }
    >
      {showForm ? (
        <div className="mb-4">
          <MasterCreateForm
            title="登记实际成本"
            fields={[
              { key: "cost_category", label: "成本项", type: "select", options: COST_CATEGORY_OPTIONS, required: true },
              { key: "amount", label: "金额", type: "text", required: true, placeholder: "如 12000" },
              { key: "source", label: "来源", type: "select", options: SOURCE_OPTIONS },
              { key: "supplier_id", label: "供应商", type: "select", options: supplierOptions },
              { key: "occurred_on", label: "发生日期", type: "text", required: true, placeholder: "YYYY-MM-DD" },
              { key: "remark", label: "备注" },
            ]}
            values={form}
            onChange={(key, value) => setForm((s) => ({ ...s, [key]: value }))}
            onSubmit={() => void handleSave()}
            onCancel={() => {
              setShowForm(false);
              setFormError(null);
            }}
            submitting={createMutation.isPending}
            error={formError}
            submitLabel="保存登记"
          />
        </div>
      ) : null}

      {rows.length ? (
        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-2 py-2 text-left font-normal">成本项</th>
                <th className="px-2 py-2 text-left font-normal">金额</th>
                <th className="px-2 py-2 text-left font-normal">来源</th>
                <th className="px-2 py-2 text-left font-normal">日期</th>
                <th className="px-2 py-2 text-left font-normal">备注</th>
                <th className="px-2 py-2 text-left font-normal">操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className={tableBodyRowClass}>
                  <td className="px-2 py-2">{categoryLabel(row.costCategory)}</td>
                  <td className="px-2 py-2 tabular-nums">{money(row.amount)}</td>
                  <td className="px-2 py-2">{row.source}</td>
                  <td className="px-2 py-2">{row.occurredOn}</td>
                  <td className="px-2 py-2 text-zinc-500">{row.remark || "—"}</td>
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      className="text-red-400 hover:underline"
                      onClick={() => void handleDelete(row.id, row.costItemName)}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-xs text-zinc-500">暂无实际成本登记，点击上方按钮添加。</p>
      )}
    </IndustrialPanel>
  );
}
