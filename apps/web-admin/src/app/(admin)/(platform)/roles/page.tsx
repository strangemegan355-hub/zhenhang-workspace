"use client";

import {
  useCreateRoleMutation,
  usePermissionsQuery,
  useRolesQuery,
  useSetRolePermissionsMutation,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { CheckboxListPanel } from "@/components/admin/checkbox-list-panel";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { useMemo, useState } from "react";

type RoleRow = {
  id: string;
  code: string;
  name: string;
  data_scope: string;
  permissions: string;
  permission_codes: string[];
  kind: string;
};

const DATA_SCOPES = ["all", "self", "department", "none"];

const defaultForm = {
  code: "",
  name: "",
  description: "",
  data_scope: "self",
};

export default function RolesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [editing, setEditing] = useState<RoleRow | null>(null);
  const [permissionSelection, setPermissionSelection] = useState<string[]>([]);
  const [assignError, setAssignError] = useState<string | null>(null);

  const query = useRolesQuery(page, search.trim() || undefined);
  const permissionsQuery = usePermissionsQuery(1);
  const createMutation = useCreateRoleMutation();
  const setPermissionsMutation = useSetRolePermissionsMutation();

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const permissionOptions = useMemo(() => {
    const items = ((permissionsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ??
      []) as Record<string, unknown>[];
    return items.map((item) => ({
      value: String(item.code ?? ""),
      label: String(item.name ?? item.code ?? ""),
      hint: String(item.code ?? ""),
    }));
  }, [permissionsQuery.data]);

  const rows = useMemo<RoleRow[]>(
    () =>
      (data.items ?? []).map((row) => {
        const codes = Array.isArray(row.permission_codes) ? (row.permission_codes as string[]) : [];
        const isSystem = Boolean(row.is_system);
        return {
          id: String(row.id ?? ""),
          code: String(row.code ?? ""),
          name: String(row.name ?? ""),
          data_scope: String(row.data_scope ?? ""),
          permissions: codes.length > 0 ? `${codes.length}` : "0",
          permission_codes: codes,
          kind: isSystem ? "系统内置" : "自定义",
        };
      }),
    [data.items],
  );

  const handleCreate = async () => {
    setFormError(null);
    const code = form.code.trim();
    if (!code) {
      setFormError("请填写角色编码");
      return;
    }
    if (!/^[a-z][a-z0-9_]*$/.test(code)) {
      setFormError("角色编码只能是小写字母、数字与下划线，且以字母开头");
      return;
    }
    if (!form.name.trim()) {
      setFormError("请填写角色名称");
      return;
    }
    if (!DATA_SCOPES.includes(form.data_scope)) {
      setFormError(`数据范围必须是 ${DATA_SCOPES.join(" / ")} 之一`);
      return;
    }
    try {
      await createMutation.mutateAsync({
        code,
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        data_scope: form.data_scope,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const savePermissions = async () => {
    if (!editing) return;
    setAssignError(null);
    try {
      await setPermissionsMutation.mutateAsync({ id: editing.id, permissionCodes: permissionSelection });
      setEditing(null);
      void query.refetch();
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "保存失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="角色管理"
        subtitle="维护角色与权限集。权限码只能由后端播种脚本创建，此页仅做分配"
        actions={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建角色</WorkspaceToolbarButton>}
      />

      {showCreate ? (
        <MasterCreateForm
          title="新建角色"
          fields={[
            { key: "code", label: "角色编码", required: true, placeholder: "如 trial_sales（小写字母/数字/下划线）" },
            { key: "name", label: "角色名称", required: true, placeholder: "如 销售" },
            { key: "data_scope", label: "数据范围", placeholder: "all / self / department / none" },
            { key: "description", label: "说明" },
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

      {editing ? (
        <CheckboxListPanel
          title={`${editing.name} 的权限集`}
          options={permissionOptions}
          selected={permissionSelection}
          onChange={setPermissionSelection}
          onSave={() => void savePermissions()}
          onCancel={() => setEditing(null)}
          submitting={setPermissionsMutation.isPending}
          error={assignError}
          searchPlaceholder="筛选权限码…"
          emptyHint="权限目录为空，请先运行后端播种脚本"
        />
      ) : null}

      <MasterListPage<RoleRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="角色管理"
        persistenceKey="platform-roles-v1"
        exportFilename="roles"
        columns={[
          { key: "code", title: "角色编码", canView: true, width: 150 },
          { key: "name", title: "名称", canView: true, width: 140 },
          { key: "data_scope", title: "数据范围", canView: true, width: 110 },
          { key: "permissions", title: "权限数", canView: true, width: 80 },
          { key: "kind", title: "类型", canView: true, width: 90 },
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
            onClick={() => {
              setEditing(row);
              setPermissionSelection(row.permission_codes);
              setAssignError(null);
            }}
          >
            编辑权限
          </button>
        )}
        emptyHint="先创建角色，再为其分配权限码"
      />
    </IndustrialPage>
  );
}
