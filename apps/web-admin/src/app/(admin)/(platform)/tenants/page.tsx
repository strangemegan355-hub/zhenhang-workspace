"use client";

import { useCreateTenantMutation, useTenantsQuery, useUpdateTenantMutation } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { useMemo, useState } from "react";

type TenantRow = {
  id: string;
  code: string;
  name: string;
  status: string;
  is_active: boolean;
};

const defaultForm = { code: "", name: "" };

export default function TenantsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const query = useTenantsQuery(page, search.trim() || undefined);
  const createMutation = useCreateTenantMutation();
  const updateMutation = useUpdateTenantMutation();

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const rows = useMemo<TenantRow[]>(
    () =>
      (data.items ?? []).map((row) => {
        const isActive = Boolean(row.is_active);
        return {
          id: String(row.id ?? ""),
          code: String(row.code ?? ""),
          name: String(row.name ?? ""),
          status: isActive ? "启用" : "停用",
          is_active: isActive,
        };
      }),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.code.trim() || !form.name.trim()) {
      setFormError("请填写租户编码与名称");
      return;
    }
    try {
      await createMutation.mutateAsync({ code: form.code.trim(), name: form.name.trim() });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const toggleActive = async (row: TenantRow) => {
    setActionError(null);
    try {
      await updateMutation.mutateAsync({ id: row.id, is_active: !row.is_active });
      void query.refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "操作失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="租户管理"
        subtitle="多租户是预留能力：当前单租户部署下，此页用于维护租户记录与启用状态"
        actions={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建租户</WorkspaceToolbarButton>}
      />

      {actionError ? <p className="text-xs text-[var(--color-danger)]">{actionError}</p> : null}

      {showCreate ? (
        <MasterCreateForm
          title="新建租户"
          fields={[
            { key: "code", label: "租户编码", required: true, placeholder: "如 zhenhang" },
            { key: "name", label: "租户名称", required: true, placeholder: "如 振航智能装备" },
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

      <MasterListPage<TenantRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="租户管理"
        persistenceKey="platform-tenants-v1"
        exportFilename="tenants"
        columns={[
          { key: "code", title: "编码", canView: true, width: 160 },
          { key: "name", title: "名称", canView: true, width: 220 },
          { key: "status", title: "状态", canView: true, width: 90 },
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
          <button
            type="button"
            className="rounded px-2 py-1 text-xs text-[var(--color-primary)] hover:bg-[var(--color-primary-soft)]"
            onClick={() => void toggleActive(row)}
          >
            {row.is_active ? "停用" : "启用"}
          </button>
        )}
        emptyHint="创建租户记录后可在用户与部门上归属"
      />
    </IndustrialPage>
  );
}
