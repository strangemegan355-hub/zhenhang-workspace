"use client";

import { useCreateMaterialMutation, useMaterialCategoriesQuery, useMaterialsQuery, useUnitsQuery } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { useMemo, useState } from "react";

type MaterialRow = {
  id: string;
  code: string;
  name: string;
  spec: string;
  unit: string;
  referencePrice: string;
};

const defaultForm = {
  code: "",
  name: "",
  spec: "",
  unit: "EA",
  reference_price: "0",
  category: "",
  remark: "",
};

export default function MaterialsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useMaterialsQuery(page, search.trim() || undefined);
  const unitsQuery = useUnitsQuery(1);
  const categoriesQuery = useMaterialCategoriesQuery(1);
  const createMutation = useCreateMaterialMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const unitOptions = useMemo(
    () =>
      ((unitsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((u) => ({
        value: String(u.code ?? ""),
        label: `${String(u.code ?? "")} · ${String(u.name ?? "")}`,
      })),
    [unitsQuery.data],
  );

  const categoryOptions = useMemo(
    () =>
      ((categoriesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c) => ({
        value: String(c.name ?? ""),
        label: `${String(c.code ?? "")} · ${String(c.name ?? "")}`,
      })),
    [categoriesQuery.data],
  );

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        code: String(row.code ?? ""),
        name: String(row.name ?? ""),
        spec: String(row.spec ?? ""),
        unit: String(row.unit ?? "EA"),
        referencePrice: String(row.reference_price ?? "0"),
      })),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.code.trim() || !form.name.trim()) {
      setFormError("请填写材料编码和名称");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: form.code.trim(),
        name: form.name.trim(),
        spec: form.spec.trim() || undefined,
        unit: form.unit.trim() || "EA",
        reference_price: Number(form.reference_price) || 0,
        category: form.category.trim() || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="材料库"
        subtitle="材料主数据统一接入页面标题与页面壳层"
        actions={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新增材料</WorkspaceToolbarButton>}
      />
      {showCreate ? (
        <MasterCreateForm
          title="新增材料"
          fields={[
            { key: "code", label: "材料编码", required: true, placeholder: "如 STEEL-Q235" },
            { key: "name", label: "材料名称", required: true, placeholder: "如 Q235钢板" },
            { key: "spec", label: "规格", placeholder: "如 10mm" },
            { key: "unit", label: "单位", type: "select", options: unitOptions, placeholder: "从基础标准选择" },
            { key: "reference_price", label: "参考单价", type: "number" },
            { key: "category", label: "分类", type: "select", options: categoryOptions, placeholder: "从基础标准选择" },
            { key: "remark", label: "备注" },
          ]}
          values={form}
          onChange={(key, value) => setForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleCreate()}
          onCancel={() => {
            setShowCreate(false);
            setFormError(null);
          }}
          submitting={createMutation.isPending}
          error={formError}
        />
      ) : null}

      <MasterListPage<MaterialRow>
        hideInternalHeader
        pageShellMode="embedded"
        embedded
        title="材料库"
        persistenceKey="master-materials-v1"
        exportFilename="materials"
        columns={[
          { key: "code", title: "编码", canView: true, fixed: "left", width: 120 },
          { key: "name", title: "名称", canView: true, width: 180 },
          { key: "spec", title: "规格", canView: true },
          { key: "unit", title: "单位", canView: true, width: 80 },
          { key: "referencePrice", title: "参考单价", canView: true, width: 100 },
        ]}
        rows={rows}
        total={data.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        toolbarExtra={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新增材料</WorkspaceToolbarButton>}
        emptyHint="材料库供成本核算选用，可先录入常用钢材、外购件"
      />
    </IndustrialPage>
  );
}
