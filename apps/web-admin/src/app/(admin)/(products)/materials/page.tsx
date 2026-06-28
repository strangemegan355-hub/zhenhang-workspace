"use client";

import {
  useCreateMaterialMutation,
  useDeleteMaterialMutation,
  useMaterialCategoriesQuery,
  useMaterialsQuery,
  useUnitsQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import {
  MaterialCategoryTree,
  type MaterialCategoryItem,
} from "@/components/materials/material-category-tree";
import { autoMasterCode } from "@/lib/auto-master-code";
import { messageBannerClass } from "@/lib/form-styles";
import { masterNameCol } from "@/lib/master-grid-columns";
import { useMemo, useState } from "react";

type MaterialRow = {
  id: string;
  name: string;
  categoryName: string;
  spec: string;
  unit: string;
  referencePrice: string;
};

const defaultForm = {
  name: "",
  spec: "",
  unit: "",
  reference_price: "0",
  remark: "",
};

export default function MaterialsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useMaterialsQuery(page, search.trim() || undefined, selectedCategoryId || undefined);
  const categoriesQuery = useMaterialCategoriesQuery(1);
  const unitsQuery = useUnitsQuery(1);
  const createMutation = useCreateMaterialMutation();
  const deleteMutation = useDeleteMaterialMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

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

  const categoryNameMap = useMemo(() => {
    const map = new Map<string, string>();
    categories.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [categories]);

  const selectedCategory = categories.find((c) => c.id === selectedCategoryId) ?? null;

  const unitOptions = useMemo(
    () =>
      ((unitsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((u) => ({
        value: String(u.code ?? ""),
        label: String(u.name ?? u.code ?? ""),
      })),
    [unitsQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        categoryName: categoryNameMap.get(String(row.category_id ?? "")) ?? String(row.category ?? "—"),
        spec: String(row.spec ?? ""),
        unit: String(row.unit ?? "—"),
        referencePrice: String(row.reference_price ?? "0"),
      })),
    [data.items, categoryNameMap],
  );

  const openCreate = () => {
    if (!selectedCategoryId) return;
    setForm({
      ...defaultForm,
      unit: unitOptions[0]?.value ?? "",
    });
    setFormError(null);
    setShowCreate(true);
  };

  const handleCreate = async () => {
    setFormError(null);
    if (!selectedCategoryId) {
      setFormError("请先在左侧选择材料分类");
      return;
    }
    if (!form.name.trim()) {
      setFormError("请填写材料名称");
      return;
    }
    if (!form.unit.trim()) {
      setFormError("请从基础标准选择单位");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "M"),
        name: form.name.trim(),
        spec: form.spec.trim() || undefined,
        unit: form.unit.trim(),
        reference_price: Number(form.reference_price) || 0,
        category_id: selectedCategoryId || undefined,
        category: selectedCategory?.name,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleBatchDelete = async (selected: MaterialRow[]) => {
    await batchDeleteRows(selected, (id) => deleteMutation.mutateAsync(id), () => void query.refetch());
  };

  const handleCategorySelect = (id: string | null) => {
    setSelectedCategoryId(id);
    setPage(1);
    if (!id) {
      setShowCreate(false);
      setFormError(null);
    }
  };

  const listColumns = useMemo(() => {
    const cols = [masterNameCol()];
    if (!selectedCategoryId) {
      cols.push({ key: "categoryName", title: "分类", canView: true, width: 120 });
    }
    cols.push(
      { key: "spec", title: "规格", canView: true, width: 140 },
      { key: "unit", title: "单位", canView: true, width: 72 },
      { key: "referencePrice", title: "参考单价", canView: true, width: 100 },
    );
    return cols;
  }, [selectedCategoryId]);

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="材料库"
        subtitle="左侧维护分类树；选中具体分类后再新建材料，单位从基础标准选择"
        actions={
          selectedCategoryId ? (
            <WorkspaceToolbarButton onClick={openCreate}>新建材料</WorkspaceToolbarButton>
          ) : null
        }
      />

      <div className="flex min-h-0 flex-1 gap-4">
        <aside className="flex w-60 shrink-0 flex-col">
          <MaterialCategoryTree
            categories={categories}
            selectedId={selectedCategoryId}
            onSelect={handleCategorySelect}
            onChanged={() => void categoriesQuery.refetch()}
            loading={categoriesQuery.isLoading}
          />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          {showCreate && selectedCategory ? (
            <>
              <div className={messageBannerClass}>
                当前分类：
                <span className="font-medium text-[var(--color-text)]">{selectedCategory.name}</span>
              </div>
              <MasterCreateForm
                title="新建材料"
                fields={[
                  { key: "name", label: "材料名称", required: true },
                  { key: "spec", label: "规格" },
                  {
                    key: "unit",
                    label: "单位",
                    type: "select",
                    required: true,
                    options: unitOptions,
                  },
                  { key: "reference_price", label: "参考单价", type: "number" },
                  { key: "remark", label: "备注" },
                ]}
                values={form}
                onChange={(key, value) => setForm((s) => ({ ...s, [key]: String(value) }))}
                onSubmit={() => void handleCreate()}
                onCancel={() => {
                  setShowCreate(false);
                  setFormError(null);
                }}
                submitting={createMutation.isPending}
                error={formError}
              />
            </>
          ) : null}

          <MasterListPage<MaterialRow>
            hideInternalHeader
            pageShellMode="embedded"
            embedded
            fill
            title={selectedCategory ? `${selectedCategory.name} · 材料列表` : "全部材料"}
            persistenceKey="master-materials-v2"
            exportFilename="materials"
            columns={listColumns}
            rows={rows}
            total={data.total ?? rows.length}
            page={page}
            onPageChange={setPage}
            search={search}
            onSearchChange={setSearch}
            query={query}
            rowKey={(row) => row.id}
            onBatchDelete={handleBatchDelete}
            toolbarExtra={
              selectedCategoryId ? (
                <WorkspaceToolbarButton onClick={openCreate}>新建材料</WorkspaceToolbarButton>
              ) : null
            }
            emptyHint={
              selectedCategory
                ? `「${selectedCategory.name}」下暂无材料，点击右上角新建材料`
                : "请先在左侧选择分类查看材料"
            }
          />
        </div>
      </div>
    </IndustrialPage>
  );
}
