"use client";

import { useCreateSupplierMutation, useDeleteSupplierMutation, useSuppliersQuery } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import { autoMasterCode } from "@/lib/auto-master-code";
import { masterNameCol } from "@/lib/master-grid-columns";
import { useMemo, useState } from "react";

type SupplierRow = {
  id: string;
  name: string;
  contactName: string;
  phone: string;
  address: string;
};

const defaultForm = {
  name: "",
  contact_name: "",
  phone: "",
  address: "",
  remark: "",
};

export default function SuppliersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useSuppliersQuery(page, search.trim() || undefined);
  const createMutation = useCreateSupplierMutation();
  const deleteMutation = useDeleteSupplierMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        contactName: String(row.contact_name ?? ""),
        phone: String(row.phone ?? ""),
        address: String(row.address ?? ""),
      })),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写供应商名称");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "S"),
        name: form.name.trim(),
        contact_name: form.contact_name.trim() || undefined,
        phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleBatchDelete = async (selected: SupplierRow[]) => {
    await batchDeleteRows(selected, (id) => deleteMutation.mutateAsync(id), () => void query.refetch());
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="供应商库"
        subtitle="供应商主数据统一接入页面标题与页面壳层"
        actions={
          <WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新增供应商</WorkspaceToolbarButton>
        }
      />
      {showCreate ? (
        <MasterCreateForm
          title="新增供应商"
          fields={[
            { key: "name", label: "供应商名称", required: true, placeholder: "如 某某钢材有限公司" },
            { key: "contact_name", label: "联系人", placeholder: "如 李经理" },
            { key: "phone", label: "联系电话", placeholder: "如 13900000000" },
            { key: "address", label: "地址", placeholder: "可选" },
            { key: "remark", label: "备注", placeholder: "供货范围、账期等" },
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

      <MasterListPage<SupplierRow>
        hideInternalHeader
        pageShellMode="embedded"
        embedded
        title="供应商库"
        persistenceKey="master-suppliers-v1"
        exportFilename="suppliers"
        columns={[
          masterNameCol(),
          { key: "contactName", title: "联系人", canView: true, width: 100 },
          { key: "phone", title: "电话", canView: true, width: 120 },
          { key: "address", title: "地址", canView: true, width: 240 },
        ]}
        rows={rows}
        total={data.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        onBatchDelete={handleBatchDelete}
        toolbarExtra={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新增供应商</WorkspaceToolbarButton>}
        emptyHint="供应商供采购询价与成本核算选用，可先录入常用钢材、外购件供应商"
      />
    </IndustrialPage>
  );
}
