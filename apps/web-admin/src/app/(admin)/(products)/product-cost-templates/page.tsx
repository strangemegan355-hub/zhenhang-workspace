"use client";

import {
  useCreateProductCostTemplateMutation,
  useDeleteProductCostTemplateMutation,
  useProductCostTemplatesQuery,
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
  scrap_rate: "0",
  overhead_rate: "0",
  line_name: "",
  line_qty: "1",
  line_cost: "0",
};

export default function ProductCostTemplatesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useProductCostTemplatesQuery(page, search.trim() || undefined);
  const productsQuery = useProductsQuery(1);
  const createMutation = useCreateProductCostTemplateMutation();
  const deleteMutation = useDeleteProductCostTemplateMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const productOptions = useMemo(
    () =>
      ((productsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: String(p.name ?? ""),
      })),
    [productsQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        lineCount: String((row.lines as unknown[] | undefined)?.length ?? 0),
        scrapRate: String(row.scrap_rate ?? "0"),
        overheadRate: String(row.overhead_rate ?? "0"),
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
          },
        ]
      : [];
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "CT"),
        name: form.name.trim(),
        product_id: form.product_id || undefined,
        scrap_rate: Number(form.scrap_rate) || 0,
        overhead_rate: Number(form.overhead_rate) || 0,
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
        title="成本模板"
        subtitle="定义产品成本构成，报价中心创建时可自动带入"
        actions={
          <WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建成本模板</WorkspaceToolbarButton>
        }
      />
      {showCreate ? (
        <MasterCreateForm
          title="新建成本模板"
          fields={[
            { key: "name", label: "模板名称", required: true },
            { key: "product_id", label: "关联产品", type: "select", options: productOptions },
            { key: "scrap_rate", label: "损耗率", type: "number" },
            { key: "overhead_rate", label: "制造费用率", type: "number" },
            { key: "line_name", label: "首行名称" },
            { key: "line_qty", label: "首行数量", type: "number" },
            { key: "line_cost", label: "首行单位成本", type: "number" },
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
        title="成本模板列表"
        exportFilename="product-cost-templates"
        columns={[
          masterNameCol(),
          { key: "lineCount", title: "行数", canView: true, width: 72 },
          { key: "scrapRate", title: "损耗率", canView: true, width: 88 },
          { key: "overheadRate", title: "费用率", canView: true, width: 88 },
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
        persistenceKey="product-cost-templates-grid"
        emptyHint="成本模板可在报价创建时自动带入"
        onBatchDelete={handleBatchDelete}
      />
    </IndustrialPage>
  );
}
