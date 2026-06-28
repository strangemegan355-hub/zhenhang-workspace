"use client";

import {
  useCreateProductPriceTemplateMutation,
  useDeleteProductPriceTemplateMutation,
  useProductCostTemplatesQuery,
  useProductPriceTemplatesQuery,
  useProductsQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import { autoMasterCode } from "@/lib/auto-master-code";
import { masterNameCol, masterStatusCol } from "@/lib/master-grid-columns";
import { useMemo, useState } from "react";

const defaultForm = {
  name: "",
  product_id: "",
  cost_template_id: "",
  margin_rate: "0.2",
  tax_rate: "0",
  line_name: "",
  line_qty: "1",
  line_cost: "0",
  line_price: "0",
};

export default function ProductPriceTemplatesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useProductPriceTemplatesQuery(page, search.trim() || undefined);
  const productsQuery = useProductsQuery(1);
  const costTemplatesQuery = useProductCostTemplatesQuery(1);
  const createMutation = useCreateProductPriceTemplateMutation();
  const deleteMutation = useDeleteProductPriceTemplateMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const productOptions = useMemo(
    () =>
      ((productsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: String(p.name ?? ""),
      })),
    [productsQuery.data],
  );

  const costTemplateOptions = useMemo(
    () =>
      ((costTemplatesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((t) => ({
        value: String(t.id ?? ""),
        label: String(t.name ?? ""),
      })),
    [costTemplatesQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        marginRate: String(row.margin_rate ?? "0.2"),
        taxRate: String(row.tax_rate ?? "0"),
        lineCount: String((row.lines as unknown[] | undefined)?.length ?? 0),
        status: String(row.status ?? "active"),
      })),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写模板名称");
      return;
    }
    const lines = form.line_name.trim()
      ? [
          {
            item_code: autoMasterCode(form.line_name.trim(), "L"),
            item_name: form.line_name.trim(),
            quantity: Number(form.line_qty) || 1,
            unit_cost: Number(form.line_cost) || 0,
            unit_price: Number(form.line_price) || 0,
          },
        ]
      : [];
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "PT"),
        name: form.name.trim(),
        product_id: form.product_id || undefined,
        cost_template_id: form.cost_template_id || undefined,
        margin_rate: Number(form.margin_rate) || 0.2,
        tax_rate: Number(form.tax_rate) || 0,
        lines,
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

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="售价模板"
        subtitle="定义毛利率与售价行，报价中心一键套用"
        actions={
          <WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建售价模板</WorkspaceToolbarButton>
        }
      />
      {showCreate ? (
        <MasterCreateForm
          title="新建售价模板"
          fields={[
            { key: "name", label: "模板名称", required: true },
            { key: "product_id", label: "关联产品", type: "select", options: productOptions },
            { key: "cost_template_id", label: "关联成本模板", type: "select", options: costTemplateOptions },
            { key: "margin_rate", label: "毛利率", type: "number" },
            { key: "tax_rate", label: "税率", type: "number" },
            { key: "line_name", label: "首行名称" },
            { key: "line_qty", label: "首行数量", type: "number" },
            { key: "line_cost", label: "首行成本", type: "number" },
            { key: "line_price", label: "首行售价", type: "number" },
          ]}
          values={form}
          onChange={(key, value) => setForm((prev) => ({ ...prev, [key]: String(value) }))}
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          submitting={createMutation.isPending}
          error={formError}
        />
      ) : null}
      <MasterListPage
        hideInternalHeader
        pageShellMode="embedded"
        embedded
        title="售价模板列表"
        exportFilename="product-price-templates"
        columns={[
          masterNameCol(),
          { key: "marginRate", title: "毛利率", canView: true, width: 88 },
          { key: "taxRate", title: "税率", canView: true, width: 72 },
          { key: "lineCount", title: "行数", canView: true, width: 72 },
          masterStatusCol(),
        ]}
        rows={rows}
        rowKey={(row) => String((row as { id: string }).id)}
        page={page}
        total={data.total ?? rows.length}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        persistenceKey="product-price-templates-grid"
        emptyHint="售价模板定义毛利率与售价行"
        onBatchDelete={handleBatchDelete}
      />
    </IndustrialPage>
  );
}
