"use client";

import { useCreateCustomerMutation, useCustomersQuery, useDeleteCustomerMutation } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import { autoMasterCode } from "@/lib/auto-master-code";
import { masterNameCol, masterStatusCol } from "@/lib/master-grid-columns";
import { useMemo, useState } from "react";

type CustomerRow = {
  id: string;
  name: string;
  industry: string;
  level: string;
  status: string;
  phone: string;
};

const defaultForm = {
  name: "",
  industry: "",
  level: "",
  phone: "",
  email: "",
  address: "",
  remarks: "",
};

export default function CustomersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useCustomersQuery(page, search.trim() || undefined);
  const createMutation = useCreateCustomerMutation();
  const deleteMutation = useDeleteCustomerMutation();
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        industry: String(row.industry ?? ""),
        level: String(row.level ?? ""),
        status: String(row.status ?? ""),
        phone: String(row.phone ?? ""),
      })),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写客户名称");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "C"),
        name: form.name.trim(),
        industry: form.industry.trim() || undefined,
        level: form.level.trim() || undefined,
        phone: form.phone.trim() || undefined,
        email: form.email.trim() || undefined,
        address: form.address.trim() || undefined,
        remarks: form.remarks.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleBatchDelete = async (selected: CustomerRow[]) => {
    await batchDeleteRows(selected, (id) => deleteMutation.mutateAsync(id), () => void query.refetch());
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="客户管理"
        subtitle="维护客户主数据，供报价与项目台账选用"
        actions={
          <WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建客户</WorkspaceToolbarButton>
        }
      />
      {showCreate ? (
        <MasterCreateForm
          title="新建客户"
          fields={[
            { key: "name", label: "客户名称", required: true, placeholder: "如 某某制造有限公司" },
            { key: "industry", label: "行业", placeholder: "如 装备制造" },
            { key: "level", label: "等级", placeholder: "如 A/B/C" },
            { key: "phone", label: "电话", placeholder: "如 13800000000" },
            { key: "email", label: "邮箱" },
            { key: "address", label: "地址" },
            { key: "remarks", label: "备注" },
          ]}
          values={form}
          onChange={(key, value) => setForm((prev) => ({ ...prev, [key]: String(value) }))}
          onSubmit={() => void handleCreate()}
          onCancel={() => {
            setShowCreate(false);
            setFormError(null);
          }}
          submitting={createMutation.isPending}
          error={formError}
        />
      ) : null}
      <MasterListPage<CustomerRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="客户管理"
        persistenceKey="master-customers-v1"
        exportFilename="customers"
        columns={[
          masterNameCol(),
          { key: "industry", title: "行业", canView: true, width: 120 },
          { key: "level", title: "等级", canView: true, width: 80 },
          masterStatusCol(),
          { key: "phone", title: "电话", canView: true, width: 120 },
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
        emptyHint="新建客户后可在报价中心与项目台账中选用"
      />
    </IndustrialPage>
  );
}
