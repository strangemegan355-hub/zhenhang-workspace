"use client";

import {
  useCreateUserMutation,
  useDepartmentsQuery,
  useRolesQuery,
  useSetUserRolesMutation,
  useUsersQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { CheckboxListPanel } from "@/components/admin/checkbox-list-panel";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { useMemo, useState } from "react";

type UserRow = {
  id: string;
  username: string;
  full_name: string;
  email: string;
  department: string;
  roles: string;
  status: string;
  is_active: boolean;
  role_codes: string[];
};

const defaultForm = {
  username: "",
  password: "",
  full_name: "",
  email: "",
};

export default function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [editing, setEditing] = useState<UserRow | null>(null);
  const [roleSelection, setRoleSelection] = useState<string[]>([]);
  const [assignError, setAssignError] = useState<string | null>(null);

  const query = useUsersQuery(page, search.trim() || undefined);
  const rolesQuery = useRolesQuery(1);
  const departmentsQuery = useDepartmentsQuery();
  const createMutation = useCreateUserMutation();
  const setRolesMutation = useSetUserRolesMutation();

  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const departments = useMemo(() => {
    const list = (departmentsQuery.data ?? []) as Record<string, unknown>[];
    return new Map(list.map((item) => [String(item.id ?? ""), String(item.name ?? "")]));
  }, [departmentsQuery.data]);

  const roleOptions = useMemo(() => {
    const items = ((rolesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []) as Record<
      string,
      unknown
    >[];
    return items.map((item) => ({
      value: String(item.code ?? ""),
      label: String(item.name ?? item.code ?? ""),
      hint: `${String(item.code ?? "")} · 数据范围 ${String(item.data_scope ?? "")}`,
    }));
  }, [rolesQuery.data]);

  const rows = useMemo<UserRow[]>(
    () =>
      (data.items ?? []).map((row) => {
        const roleCodes = Array.isArray(row.role_codes) ? (row.role_codes as string[]) : [];
        const isActive = Boolean(row.is_active);
        return {
          id: String(row.id ?? ""),
          username: String(row.username ?? ""),
          full_name: String(row.full_name ?? ""),
          email: String(row.email ?? ""),
          department: departments.get(String(row.department_id ?? "")) ?? "—",
          roles: roleCodes.length > 0 ? roleCodes.join("、") : "—",
          status: isActive ? "启用" : "停用",
          is_active: isActive,
          role_codes: roleCodes,
        };
      }),
    [data.items, departments],
  );

  const handleCreate = async () => {
    setFormError(null);
    if (!form.username.trim()) {
      setFormError("请填写用户名");
      return;
    }
    if (form.password.length < 8) {
      setFormError("密码至少 8 位");
      return;
    }
    try {
      await createMutation.mutateAsync({
        username: form.username.trim(),
        password: form.password,
        full_name: form.full_name.trim() || undefined,
        email: form.email.trim() || undefined,
      });
      setForm(defaultForm);
      setShowCreate(false);
      void query.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const openRoleEditor = (row: UserRow) => {
    setEditing(row);
    setRoleSelection(row.role_codes);
    setAssignError(null);
  };

  const saveRoles = async () => {
    if (!editing) return;
    setAssignError(null);
    try {
      await setRolesMutation.mutateAsync({ id: editing.id, roleCodes: roleSelection });
      setEditing(null);
      void query.refetch();
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "保存失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="用户管理"
        subtitle="创建账号并分配角色。仅超级用户可访问本页，角色的权限由「角色管理」维护"
        actions={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建用户</WorkspaceToolbarButton>}
      />

      {showCreate ? (
        <MasterCreateForm
          title="新建用户"
          fields={[
            { key: "username", label: "用户名", required: true, placeholder: "如 sales02" },
            { key: "password", label: "初始密码", required: true, placeholder: "至少 8 位" },
            { key: "full_name", label: "姓名", placeholder: "如 销售小王" },
            { key: "email", label: "邮箱" },
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
          title={`为 ${editing.username} 分配角色`}
          options={roleOptions}
          selected={roleSelection}
          onChange={setRoleSelection}
          onSave={() => void saveRoles()}
          onCancel={() => setEditing(null)}
          submitting={setRolesMutation.isPending}
          error={assignError}
          searchPlaceholder="筛选角色…"
          emptyHint="尚无角色，请先在「角色管理」中创建"
        />
      ) : null}

      <MasterListPage<UserRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="用户管理"
        persistenceKey="platform-users-v1"
        exportFilename="users"
        columns={[
          { key: "username", title: "用户名", canView: true, width: 140 },
          { key: "full_name", title: "姓名", canView: true, width: 120 },
          { key: "department", title: "部门", canView: true, width: 120 },
          { key: "roles", title: "角色", canView: true, width: 220 },
          { key: "status", title: "状态", canView: true, width: 80 },
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
            onClick={() => openRoleEditor(row)}
          >
            分配角色
          </button>
        )}
        emptyHint="新建用户后在此分配角色；密码可在后端重置"
      />
    </IndustrialPage>
  );
}
