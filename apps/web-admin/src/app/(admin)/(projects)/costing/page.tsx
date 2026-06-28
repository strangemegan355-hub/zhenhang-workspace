"use client";

import { MasterListPage } from "@/components/master/master-list-page";
import {
  useBusinessSettingsQuery,
  useCostEstimateQuery,
  useCostEstimatesQuery,
  useCreateCostEstimateMutation,
  useDeleteCostEstimateMutation,
  useMaterialCategoriesQuery,
  useMaterialsQuery,
  usePreviewCostEstimateMutation,
  useUnitsQuery,
  useUpdateCostEstimateMutation,
  type CostEstimatePayload,
  type CostEstimateSummary,
  type CostLineMaterial,
  type CostLineProcess,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, WorkspaceToolbarButton, typography } from "@zhenhang/ui";
import { MaterialCategoryCascader } from "@/components/materials/material-category-cascader";
import type { MaterialCategoryItem } from "@/components/materials/material-category-tree";
import { getCategoryPath, resolveLeafCategoryId } from "@/lib/material-category-utils";
import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import {
  dangerActionClass,
  fieldInputClass,
  fieldLabelClass,
  linkActionClass,
  tableBodyRowClass,
  tableHeaderRowClass,
} from "@/lib/form-styles";

type ListRow = {
  id: string;
  estimateNo: string;
  productName: string;
  qty: string;
  status: string;
  totalCost: string;
  finalTotal: string;
};

type MaterialCatalogItem = {
  id: string;
  name: string;
  spec: string;
  unit: string;
  price: number;
  category_id: string;
};

function applyMaterialVariant(line: CostLineMaterial, material: MaterialCatalogItem): CostLineMaterial {
  return {
    ...line,
    material_id: material.id,
    category_id: material.category_id,
    name: material.name,
    spec: material.spec,
    unit: material.unit,
    unit_price: material.price,
  };
}

function toApiPayload(form: CostEstimatePayload): CostEstimatePayload {
  return {
    ...form,
    material_lines: form.material_lines.map(
      ({ category_id: _categoryId, category_path: _categoryPath, ...line }) => line,
    ),
  };
}

const emptyForm: CostEstimatePayload = {
  product_name: "",
  product_spec: "",
  power_kw: "",
  qty: 1,
  remark: "",
  outsource_cost: 0,
  logistics_cost: 0,
  material_lines: [],
  machine_lines: [],
  process_lines: [],
};

const emptySummary: CostEstimateSummary = {
  material_cost: 0,
  machine_cost: 0,
  labor_cost: 0,
  other_cost: 0,
  base_cost: 0,
  scrap_cost: 0,
  overhead_cost: 0,
  total_cost: 0,
  profit_amount: 0,
  before_tax: 0,
  tax_amount: 0,
  final_total: 0,
  unit_final: 0,
};

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function LineTable({
  title,
  headers,
  rows,
  onAdd,
  renderRow,
}: {
  title: string;
  headers: string[];
  rows: number[];
  onAdd: () => void;
  renderRow: (index: number) => ReactNode;
}) {
  return (
    <IndustrialPanel title={title} toolbar={<WorkspaceToolbarButton onClick={onAdd}>添加行</WorkspaceToolbarButton>}>
      <div className="overflow-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className={tableHeaderRowClass}>
              {headers.map((h) => (
                <th key={h} className="px-2 py-2 text-left font-normal">
                  {h}
                </th>
              ))}
              <th className="px-2 py-2 text-left font-normal">操作</th>
            </tr>
          </thead>
          <tbody>{rows.map((idx) => renderRow(idx))}</tbody>
        </table>
      </div>
    </IndustrialPanel>
  );
}

function detailToCostForm(
  d: Record<string, unknown>,
  settings?: { default_scrap_rate?: number; default_overhead_rate?: number; default_profit_rate?: number; default_tax_rate?: number } | null,
): { form: CostEstimatePayload; summary: CostEstimateSummary } {
  return {
    form: {
      product_name: String(d.product_name ?? ""),
      product_spec: String(d.product_spec ?? ""),
      power_kw: String(d.power_kw ?? ""),
      qty: Number(d.qty ?? 1),
      remark: String(d.remark ?? ""),
      outsource_cost: Number(d.outsource_cost ?? 0),
      logistics_cost: Number(d.logistics_cost ?? 0),
      scrap_rate: Number(d.scrap_rate ?? settings?.default_scrap_rate ?? 0),
      overhead_rate: Number(d.overhead_rate ?? settings?.default_overhead_rate ?? 0),
      profit_rate: Number(d.profit_rate ?? settings?.default_profit_rate ?? 20),
      tax_rate: Number(d.tax_rate ?? settings?.default_tax_rate ?? 13),
      material_lines: ((d.material_lines as Record<string, unknown>[]) ?? []).map((line) => ({
        material_id: line.material_id ? String(line.material_id) : undefined,
        name: String(line.name ?? ""),
        spec: String(line.spec ?? ""),
        qty: Number(line.qty ?? 1),
        unit: String(line.unit ?? "EA"),
        unit_price: Number(line.unit_price ?? 0),
      })),
      machine_lines: ((d.machine_lines as Record<string, unknown>[]) ?? []).map((line) => ({
        machine_id: line.machine_id ? String(line.machine_id) : undefined,
        name: String(line.name ?? ""),
        spec: String(line.spec ?? ""),
        power_kw: String(line.power_kw ?? ""),
        qty: Number(line.qty ?? 1),
        unit_price: Number(line.unit_price ?? 0),
      })),
      process_lines: ((d.process_lines as Record<string, unknown>[]) ?? []).map((line) => ({
        process_name: String(line.process_name ?? ""),
        equipment: String(line.equipment ?? ""),
        hours: Number(line.hours ?? 0),
        rate: Number(line.rate ?? 0),
      })),
    },
    summary: {
      material_cost: Number(d.material_cost ?? 0),
      machine_cost: Number(d.machine_cost ?? 0),
      labor_cost: Number(d.labor_cost ?? 0),
      other_cost: Number(d.other_cost ?? 0),
      base_cost: Number(d.base_cost ?? 0),
      scrap_cost: Number(d.scrap_cost ?? 0),
      overhead_cost: Number(d.overhead_cost ?? 0),
      total_cost: Number(d.total_cost ?? 0),
      profit_amount: Number(d.profit_amount ?? 0),
      before_tax: Number(d.before_tax ?? 0),
      tax_amount: Number(d.tax_amount ?? 0),
      final_total: Number(d.final_total ?? 0),
      unit_final: Number(d.unit_final ?? 0),
    },
  };
}

export default function CostingPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<"list" | "edit">("list");
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<CostEstimatePayload>(emptyForm);
  const [summary, setSummary] = useState<CostEstimateSummary>(emptySummary);
  const [formError, setFormError] = useState<string | null>(null);
  const [formHydrationKey, setFormHydrationKey] = useState("list");

  const listQuery = useCostEstimatesQuery(page, search.trim() || undefined);
  const detailQuery = useCostEstimateQuery(editId ?? undefined);
  const materialsQuery = useMaterialsQuery(1);
  const categoriesQuery = useMaterialCategoriesQuery(1);
  const unitsQuery = useUnitsQuery(1);
  const settingsQuery = useBusinessSettingsQuery();
  const previewMutation = usePreviewCostEstimateMutation();
  const createMutation = useCreateCostEstimateMutation();
  const updateMutation = useUpdateCostEstimateMutation();
  const deleteMutation = useDeleteCostEstimateMutation();

  const listData = (listQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const materialCatalog = useMemo<MaterialCatalogItem[]>(
    () =>
      ((materialsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        id: String(m.id ?? ""),
        name: String(m.name ?? ""),
        spec: String(m.spec ?? ""),
        unit: String(m.unit ?? "EA"),
        price: Number(m.reference_price ?? 0),
        category_id: String(m.category_id ?? ""),
      })),
    [materialsQuery.data],
  );

  const categories = useMemo<MaterialCategoryItem[]>(
    () =>
      ((categoriesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c) => ({
        id: String(c.id ?? ""),
        code: String(c.code ?? ""),
        name: String(c.name ?? ""),
        parent_id: c.parent_id ? String(c.parent_id) : null,
      })),
    [categoriesQuery.data],
  );

  const unitOptions = useMemo(
    () =>
      ((unitsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((u) => ({
        value: String(u.code ?? ""),
        label: String(u.name ?? u.code ?? ""),
      })),
    [unitsQuery.data],
  );

  const defaultUnit = unitOptions[0]?.value ?? "EA";

  // ponytail: derive display lines from form + catalog — avoids setState-in-effect (ESLint react-hooks/set-state-in-effect)
  const displayMaterialLines = useMemo(
    () =>
      form.material_lines.map((line) => {
        let categoryId = line.category_id;
        if (line.material_id && !categoryId) {
          const mat = materialCatalog.find((m) => m.id === line.material_id);
          categoryId = mat?.category_id;
        }
        const categoryPath =
          categoryId && categories.length > 0 ? getCategoryPath(categories, categoryId) : line.category_path;
        return { ...line, category_id: categoryId, category_path: categoryPath };
      }),
    [form.material_lines, materialCatalog, categories],
  );

  const rows = useMemo(
    () =>
      (listData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        estimateNo: String(row.estimate_no ?? ""),
        productName: String(row.product_name ?? ""),
        qty: String(row.qty ?? "1"),
        status: String(row.status ?? "draft") === "draft" ? "草稿" : String(row.status ?? ""),
        totalCost: money(row.total_cost as number | string),
        finalTotal: money(row.final_total as number | string),
      })),
    [listData.items],
  );

  const targetHydrationKey =
    mode === "edit"
      ? editId
        ? detailQuery.data
          ? `edit:${editId}:${detailQuery.dataUpdatedAt}`
          : "edit:pending"
        : "create"
      : "list";

  if (
    targetHydrationKey !== "list" &&
    targetHydrationKey !== "edit:pending" &&
    targetHydrationKey !== formHydrationKey
  ) {
    setFormHydrationKey(targetHydrationKey);
    if (targetHydrationKey === "create") {
      const s = settingsQuery.data;
      setForm({
        ...emptyForm,
        scrap_rate: Number(s?.default_scrap_rate ?? 0),
        overhead_rate: Number(s?.default_overhead_rate ?? 0),
        profit_rate: Number(s?.default_profit_rate ?? 20),
        tax_rate: Number(s?.default_tax_rate ?? 13),
      });
      setSummary(emptySummary);
    } else if (detailQuery.data) {
      const mapped = detailToCostForm(detailQuery.data as Record<string, unknown>, settingsQuery.data);
      setForm(mapped.form);
      setSummary(mapped.summary);
    }
  }

  const openCreate = () => {
    const s = settingsQuery.data;
    setEditId(null);
    setForm({
      ...emptyForm,
      scrap_rate: Number(s?.default_scrap_rate ?? 0),
      overhead_rate: Number(s?.default_overhead_rate ?? 0),
      profit_rate: Number(s?.default_profit_rate ?? 20),
      tax_rate: Number(s?.default_tax_rate ?? 13),
    });
    setSummary(emptySummary);
    setFormError(null);
    setMode("edit");
  };

  const openEdit = (id: string) => {
    setEditId(id);
    setFormError(null);
    setMode("edit");
  };

  const backToList = () => {
    setMode("list");
    setEditId(null);
    setForm(emptyForm);
    setSummary(emptySummary);
    setFormHydrationKey("list");
    void listQuery.refetch();
  };

  const runPreview = async (payload: CostEstimatePayload) => {
    try {
      const result = await previewMutation.mutateAsync(toApiPayload(payload));
      setSummary(result);
    } catch {
      /* keep previous summary */
    }
  };

  const updateForm = (patch: Partial<CostEstimatePayload>) => {
    setForm((prev) => {
      const next = { ...prev, ...patch };
      void runPreview(next);
      return next;
    });
  };

  const updateMaterialLine = (index: number, patch: Partial<CostLineMaterial>) => {
    setForm((prev) => {
      const lines = [...prev.material_lines];
      lines[index] = { ...lines[index], ...patch };
      const next = { ...prev, material_lines: lines };
      void runPreview(next);
      return next;
    });
  };

  const updateProcessLine = (index: number, patch: Partial<CostLineProcess>) => {
    setForm((prev) => {
      const lines = [...prev.process_lines];
      lines[index] = { ...lines[index], ...patch };
      const next = { ...prev, process_lines: lines };
      void runPreview(next);
      return next;
    });
  };

  const pickMaterialCategoryPath = (index: number, path: string[]) => {
    const category_id = resolveLeafCategoryId(categories, path);
    updateMaterialLine(index, {
      category_path: path,
      category_id,
      material_id: undefined,
      name: "",
      spec: "",
      unit: defaultUnit,
      unit_price: 0,
    });
  };

  const pickMaterialName = (index: number, name: string) => {
    const line = form.material_lines[index];
    const variants = materialCatalog.filter((m) => m.category_id === line.category_id && m.name === name);
    let next: CostLineMaterial = {
      ...line,
      name,
      material_id: undefined,
      spec: "",
      unit: defaultUnit,
      unit_price: 0,
    };
    if (variants.length === 1) {
      next = applyMaterialVariant(next, variants[0]!);
    }
    updateMaterialLine(index, next);
  };

  const pickMaterialSpec = (index: number, materialId: string) => {
    const mat = materialCatalog.find((m) => m.id === materialId);
    if (!mat) return;
    const next = applyMaterialVariant(form.material_lines[index], mat);
    updateMaterialLine(index, {
      ...next,
      category_path: mat.category_id ? getCategoryPath(categories, mat.category_id) : next.category_path,
    });
  };

  const handleSave = async () => {
    setFormError(null);
    if (!form.product_name.trim()) {
      setFormError("请填写产品名称");
      return;
    }
    const payload: CostEstimatePayload = {
      ...toApiPayload(form),
      machine_lines: [],
      product_name: form.product_name.trim(),
      product_spec: form.product_spec?.trim() || undefined,
      power_kw: form.power_kw?.trim() || undefined,
      remark: form.remark?.trim() || undefined,
      qty: Number(form.qty) || 1,
    };
    try {
      if (editId) await updateMutation.mutateAsync({ id: editId, body: payload });
      else await createMutation.mutateAsync(payload);
      backToList();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`确认删除成本核算单「${label}」？`)) return;
    try {
      await deleteMutation.mutateAsync(id);
      void listQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  if (mode === "edit") {
    if (editId && !detailQuery.data) {
      return (
        <IndustrialPage gap="md" fill>
          <IndustrialPanel fill title="编辑成本核算">
            <p className="text-sm text-[var(--color-text-muted)]">加载核算单详情…</p>
          </IndustrialPanel>
        </IndustrialPage>
      );
    }

    return (
      <IndustrialPage gap="md" fill>
        <div className="flex items-center justify-between gap-2">
          <h2 className={typography.pageTitle}>{editId ? "编辑成本核算" : "新建成本核算"}</h2>
          <div className="flex gap-2">
            <WorkspaceToolbarButton onClick={backToList}>返回列表</WorkspaceToolbarButton>
            <button
              type="button"
              disabled={createMutation.isPending || updateMutation.isPending}
              onClick={() => void handleSave()}
              className="btn-primary h-8 px-4 text-xs disabled:opacity-60"
            >
              {createMutation.isPending || updateMutation.isPending ? "保存中…" : "保存核算单"}
            </button>
          </div>
        </div>

        {formError ? <p className="text-xs text-red-500">{formError}</p> : null}

        <IndustrialPanel title="基本信息">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>产品名称 *</span>
              <input
                className={fieldInputClass}
                value={form.product_name}
                onChange={(e) => updateForm({ product_name: e.target.value })}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>规格型号</span>
              <input
                className={fieldInputClass}
                value={form.product_spec ?? ""}
                onChange={(e) => updateForm({ product_spec: e.target.value })}
                placeholder="如 型号、尺寸"
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>功率</span>
              <input
                className={fieldInputClass}
                value={form.power_kw ?? ""}
                onChange={(e) => updateForm({ power_kw: e.target.value })}
                placeholder="如 55kW"
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>数量</span>
              <input
                type="number"
                className={fieldInputClass}
                value={form.qty}
                onChange={(e) => updateForm({ qty: Number(e.target.value) || 1 })}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2 lg:col-span-4">
              <span className={fieldLabelClass}>备注</span>
              <input className={fieldInputClass} value={form.remark ?? ""} onChange={(e) => updateForm({ remark: e.target.value })} />
            </label>
          </div>
        </IndustrialPanel>

        {materialCatalog.length === 0 ? (
          <p className="text-xs text-[var(--color-text-muted)]">
            暂无材料库数据，请先在
            <Link href="/materials" className={`mx-1 ${linkActionClass}`}>
              材料库
            </Link>
            维护分类与材料后再选料。
          </p>
        ) : (
          <p className="text-xs text-[var(--color-text-muted)]">
            添加行后请按材料库分类逐级选择：一级分类 → 下级分类 → 名称 → 规格；数据来自
            <Link href="/materials" className={`mx-1 ${linkActionClass}`}>
              材料库
            </Link>
            。
          </p>
        )}

        <LineTable
          title="材料明细"
          headers={["分类", "名称", "规格", "数量", "单位", "单价", "行金额"]}
          rows={displayMaterialLines.map((_, i) => i)}
          onAdd={() =>
            updateForm({
              material_lines: [...form.material_lines, { name: "", qty: 1, unit: defaultUnit, unit_price: 0 }],
            })
          }
          renderRow={(idx) => {
            const line = displayMaterialLines[idx];
            const lineTotal = (line.qty || 0) * (line.unit_price || 0);
            const categoryMaterials = materialCatalog.filter((m) => m.category_id === line.category_id);
            const nameOptions = [
              ...new Set(categoryMaterials.map((m) => m.name).filter(Boolean)),
            ].sort((a, b) => a.localeCompare(b, "zh-CN"));
            const specVariants = categoryMaterials.filter((m) => m.name === line.name);
            return (
              <tr key={idx} className={tableBodyRowClass}>
                <td className="px-2 py-1 align-top">
                  <MaterialCategoryCascader
                    categories={categories}
                    path={line.category_path ?? []}
                    onPathChange={(path) => pickMaterialCategoryPath(idx, path)}
                  />
                </td>
                <td className="px-2 py-1">
                  <select
                    className={fieldInputClass}
                    value={line.name}
                    disabled={!line.category_id}
                    onChange={(e) => pickMaterialName(idx, e.target.value)}
                  >
                    <option value="">选择名称</option>
                    {nameOptions.map((name) => (
                      <option key={name} value={name}>
                        {name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1">
                  <select
                    className={fieldInputClass}
                    value={line.material_id ?? ""}
                    disabled={!line.name}
                    onChange={(e) => pickMaterialSpec(idx, e.target.value)}
                  >
                    <option value="">选择规格</option>
                    {specVariants.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.spec || "—"}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1">
                  <input type="number" className={fieldInputClass} value={line.qty} onChange={(e) => updateMaterialLine(idx, { qty: Number(e.target.value) || 0 })} />
                </td>
                <td className="px-2 py-1">
                  <select className={fieldInputClass} value={line.unit} onChange={(e) => updateMaterialLine(idx, { unit: e.target.value })}>
                    <option value="">请选择</option>
                    {unitOptions.map((u) => (
                      <option key={u.value} value={u.value}>
                        {u.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1">
                  <input type="number" className={fieldInputClass} value={line.unit_price} onChange={(e) => updateMaterialLine(idx, { unit_price: Number(e.target.value) || 0 })} />
                </td>
                <td className="px-2 py-1 text-[var(--color-text)]">{money(lineTotal)}</td>
                <td className="px-2 py-1">
                  <button type="button" className={dangerActionClass} onClick={() => updateForm({ material_lines: form.material_lines.filter((_, i) => i !== idx) })}>
                    删除
                  </button>
                </td>
              </tr>
            );
          }}
        />

        <LineTable
          title="工序明细"
          headers={["工序", "设备", "工时", "费率", "行金额"]}
          rows={form.process_lines.map((_, i) => i)}
          onAdd={() =>
            updateForm({
              process_lines: [...form.process_lines, { process_name: "", hours: 0, rate: 0 }],
            })
          }
          renderRow={(idx) => {
            const line = form.process_lines[idx];
            const lineTotal = (line.hours || 0) * (line.rate || 0);
            return (
              <tr key={idx} className={tableBodyRowClass}>
                <td className="px-2 py-1">
                  <input className={fieldInputClass} value={line.process_name} onChange={(e) => updateProcessLine(idx, { process_name: e.target.value })} />
                </td>
                <td className="px-2 py-1">
                  <input className={fieldInputClass} value={line.equipment ?? ""} onChange={(e) => updateProcessLine(idx, { equipment: e.target.value })} />
                </td>
                <td className="px-2 py-1">
                  <input type="number" className={fieldInputClass} value={line.hours} onChange={(e) => updateProcessLine(idx, { hours: Number(e.target.value) || 0 })} />
                </td>
                <td className="px-2 py-1">
                  <input type="number" className={fieldInputClass} value={line.rate} onChange={(e) => updateProcessLine(idx, { rate: Number(e.target.value) || 0 })} />
                </td>
                <td className="px-2 py-1 text-[var(--color-text)]">{money(lineTotal)}</td>
                <td className="px-2 py-1">
                  <button type="button" className={dangerActionClass} onClick={() => updateForm({ process_lines: form.process_lines.filter((_, i) => i !== idx) })}>
                    删除
                  </button>
                </td>
              </tr>
            );
          }}
        />

        <IndustrialPanel title="费用与费率">
          <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
            {(
              [
                ["outsource_cost", "外协费用"],
                ["logistics_cost", "物流费用"],
                ["scrap_rate", "废品率(%)"],
                ["overhead_rate", "管理费率(%)"],
                ["profit_rate", "利润率(%)"],
                ["tax_rate", "税率(%)"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>{label}</span>
                <input
                  type="number"
                  className={fieldInputClass}
                  value={form[key] ?? 0}
                  onChange={(e) => updateForm({ [key]: Number(e.target.value) || 0 })}
                />
              </label>
            ))}
          </div>
        </IndustrialPanel>

        <IndustrialPanel title="成本汇总">
          <div className="grid gap-2 text-xs md:grid-cols-2 lg:grid-cols-4">
            <div>材料成本：{money(summary.material_cost)}</div>
            <div>工序人工：{money(summary.labor_cost)}</div>
            <div>其他费用：{money(summary.other_cost)}</div>
            <div>基础成本：{money(summary.base_cost)}</div>
            <div>废品成本：{money(summary.scrap_cost)}</div>
            <div>管理费用：{money(summary.overhead_cost)}</div>
            <div className="font-semibold text-[var(--color-success)]">完全成本：{money(summary.total_cost)}</div>
            <div>利润：{money(summary.profit_amount)}</div>
            <div>税前合计：{money(summary.before_tax)}</div>
            <div>税额：{money(summary.tax_amount)}</div>
            <div className="font-semibold text-[var(--color-primary)]">含税总价：{money(summary.final_total)}</div>
            <div className="md:col-span-2">单件含税价：{money(summary.unit_final)}</div>
          </div>
          {previewMutation.isPending ? <p className="mt-2 text-xs text-[var(--color-text-muted)]">汇总计算中…</p> : null}
        </IndustrialPanel>
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md" fill>
      <MasterListPage<ListRow>
        embedded
        fill
        title="成本核算"
        persistenceKey="cost-estimates-v1"
        exportFilename="cost-estimates"
        columns={[
          { key: "estimateNo", title: "单号", canView: true, fixed: "left", width: 160 },
          { key: "productName", title: "产品名称", canView: true, width: 180 },
          { key: "qty", title: "数量", canView: true, width: 80 },
          { key: "totalCost", title: "完全成本", canView: true },
          { key: "finalTotal", title: "含税总价", canView: true },
          { key: "status", title: "状态", canView: true, width: 80 },
        ]}
        rows={rows}
        total={listData.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={listQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-2">
            <button type="button" className={linkActionClass} onClick={() => openEdit(row.id)}>
              修改
            </button>
            <button type="button" className={dangerActionClass} onClick={() => void handleDelete(row.id, row.productName)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreate}>新建核算</WorkspaceToolbarButton>}
        emptyHint="材料与工序成本在此汇总为完全成本；对客报价请在报价中心从产品库选型"
      />
    </IndustrialPage>
  );
}
