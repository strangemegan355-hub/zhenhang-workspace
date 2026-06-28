"use client";

import {
  useCreateProductMutation,
  useDeleteProductMutation,
  useProductCategoriesQuery,
  useProductCostTemplatesQuery,
  useProductPriceTemplatesQuery,
  useProductsQuery,
  useUnitsQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import {
  ProductCategoryTree,
  type ProductCategoryItem,
} from "@/components/products/product-category-tree";
import { autoMasterCode } from "@/lib/auto-master-code";
import { messageBannerClass } from "@/lib/form-styles";
import { masterNameCol, masterStatusCol } from "@/lib/master-grid-columns";
import { isMotorCategory, productSpecLabel, productSpecPlaceholder } from "@/lib/product-category-labels";
import { useMemo, useState } from "react";

const defaultForm = {
  name: "",
  spec: "",
  unit: "",
  reference_cost: "0",
  reference_price: "0",
  default_cost_template_id: "",
  default_price_template_id: "",
  remark: "",
};

export default function ProductsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useProductsQuery(page, search.trim() || undefined, selectedCategoryId || undefined);
  const categoriesQuery = useProductCategoriesQuery(1);
  const unitsQuery = useUnitsQuery(1);
  const costTemplatesQuery = useProductCostTemplatesQuery(1);
  const priceTemplatesQuery = useProductPriceTemplatesQuery(1);
  const createMutation = useCreateProductMutation();
  const deleteMutation = useDeleteProductMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const categories = useMemo<ProductCategoryItem[]>(
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
  const specLabel = productSpecLabel(selectedCategory?.name);
  const specPlaceholder = productSpecPlaceholder(selectedCategory?.name);
  const productsSubtitle = selectedCategory
    ? isMotorCategory(selectedCategory.name)
      ? `「${selectedCategory.name}」：规格栏填功率（如 55kW），参考售价为对客单价`
      : `「${selectedCategory.name}」：规格栏填规格型号，参考售价为对客单价`
    : "左侧选择分类；电机类填功率，其他分类填规格型号，参考售价为对客单价";

  const unitOptions = useMemo(
    () =>
      ((unitsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((u) => ({
        value: String(u.code ?? ""),
        label: String(u.name ?? u.code ?? ""),
      })),
    [unitsQuery.data],
  );

  const costTemplateOptions = useMemo(
    () =>
      ((costTemplatesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((t) => ({
        value: String(t.id ?? ""),
        label: String(t.name ?? ""),
      })),
    [costTemplatesQuery.data],
  );

  const priceTemplateOptions = useMemo(
    () =>
      ((priceTemplatesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((t) => ({
        value: String(t.id ?? ""),
        label: String(t.name ?? ""),
      })),
    [priceTemplatesQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        categoryName: categoryNameMap.get(String(row.category_id ?? "")) ?? "—",
        spec: String(row.spec ?? ""),
        unit: String(row.unit ?? "—"),
        referenceCost: String(row.reference_cost ?? "0"),
        referencePrice: String(row.reference_price ?? "0"),
        status: String(row.status ?? "active"),
      })),
    [data.items, categoryNameMap],
  );

  const openCreate = () => {
    setForm({
      ...defaultForm,
      unit: unitOptions[0]?.value ?? "",
    });
    setFormError(null);
    setShowCreate(true);
  };

  const handleCreate = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写产品名称");
      return;
    }
    if (!form.unit.trim()) {
      setFormError("请从基础标准选择单位");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "P"),
        name: form.name.trim(),
        category_id: selectedCategoryId || undefined,
        spec: form.spec.trim() || undefined,
        unit: form.unit.trim(),
        reference_cost: Number(form.reference_cost) || 0,
        reference_price: Number(form.reference_price) || 0,
        default_cost_template_id: form.default_cost_template_id || undefined,
        default_price_template_id: form.default_price_template_id || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleBatchDelete = async (selected: typeof rows) => {
    await batchDeleteRows(selected, (id) => deleteMutation.mutateAsync(id), () => void query.refetch());
  };

  const handleCategorySelect = (id: string | null) => {
    setSelectedCategoryId(id);
    setPage(1);
  };

  const listColumns = useMemo(() => {
    const cols = [masterNameCol()];
    if (!selectedCategoryId) {
      cols.push({ key: "categoryName", title: "分类", canView: true, width: 120 });
    }
    cols.push(
      { key: "spec", title: specLabel, canView: true, width: 120 },
      { key: "unit", title: "单位", canView: true, width: 72 },
      { key: "referenceCost", title: "参考成本", canView: true, width: 100 },
      { key: "referencePrice", title: "参考售价", canView: true, width: 100 },
      masterStatusCol(),
    );
    return cols;
  }, [selectedCategoryId, specLabel]);

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="产品库"
        subtitle={productsSubtitle}
        actions={<WorkspaceToolbarButton onClick={openCreate}>新建产品</WorkspaceToolbarButton>}
      />

      <div className="flex min-h-0 flex-1 gap-4">
        <aside className="flex w-60 shrink-0 flex-col">
          <ProductCategoryTree
            categories={categories}
            selectedId={selectedCategoryId}
            onSelect={handleCategorySelect}
            onChanged={() => void categoriesQuery.refetch()}
            loading={categoriesQuery.isLoading}
          />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          {showCreate ? (
            <>
              <div className={messageBannerClass}>
                当前分类：
                <span className="font-medium text-[var(--color-text)]">
                  {selectedCategory ? selectedCategory.name : "未选择（产品将不归入任何分类）"}
                </span>
                {!selectedCategory ? (
                  <span className="ml-2 text-[var(--color-text-muted)]">— 请先在左侧树中点击分类</span>
                ) : null}
              </div>
              <MasterCreateForm
                title="新建产品"
                fields={[
                  { key: "name", label: "产品名称", required: true, placeholder: "如 XX系列电机" },
                  { key: "spec", label: specLabel, placeholder: specPlaceholder },
                  {
                    key: "unit",
                    label: "单位",
                    type: "select",
                    required: true,
                    options: unitOptions,
                    placeholder: unitOptions.length === 0 ? "请先在「基础标准」维护单位" : "从基础标准选择",
                  },
                  { key: "reference_cost", label: "参考成本", type: "number" },
                  { key: "reference_price", label: "参考售价（对客单价）", type: "number" },
                  {
                    key: "default_cost_template_id",
                    label: "默认成本模板",
                    type: "select",
                    options: costTemplateOptions,
                  },
                  {
                    key: "default_price_template_id",
                    label: "默认售价模板",
                    type: "select",
                    options: priceTemplateOptions,
                  },
                  { key: "remark", label: "备注" },
                ]}
                values={form}
                onChange={(key, value) => setForm((prev) => ({ ...prev, [key]: String(value) }))}
                onSubmit={handleCreate}
                onCancel={() => setShowCreate(false)}
                submitting={createMutation.isPending}
                error={formError}
              />
            </>
          ) : null}

          <MasterListPage
            hideInternalHeader
            pageShellMode="embedded"
            embedded
            fill
            title={selectedCategory ? `${selectedCategory.name} · 产品列表` : "全部产品"}
            exportFilename="products"
            columns={listColumns}
            rows={rows}
            rowKey={(row) => String((row as { id: string }).id)}
            page={page}
            total={data.total ?? rows.length}
            onPageChange={setPage}
            search={search}
            onSearchChange={setSearch}
            query={query}
            persistenceKey="products-grid"
            emptyHint={
              selectedCategory
                ? `「${selectedCategory.name}」下暂无产品，点击右上角新建产品`
                : "请先在左侧选择分类，或查看全部产品"
            }
            onBatchDelete={handleBatchDelete}
          />
        </div>
      </div>
    </IndustrialPage>
  );
}
