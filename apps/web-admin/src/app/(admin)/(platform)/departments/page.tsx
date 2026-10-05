"use client";

import { useCreateDepartmentMutation, useDepartmentsQuery } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import { MasterListPage } from "@/components/master/master-list-page";
import { fieldInputClass } from "@/lib/form-styles";
import { useMemo, useState } from "react";

type DepartmentRow = {
  id: string;
  code: string;
  name: string;
  parent: string;
  sort_order: string;
  users: string;
};

const defaultForm = { code: "", name: "", parent_id: "", sort_order: "0", description: "" };

export default function DepartmentsPage() {
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);

  const query = useDepartmentsQuery();
  const createMutation = useCreateDepartmentMutation();

  const raw = useMemo(() => (query.data ?? []) as Record<string, unknown>[], [query.data]);

  const names = useMemo(
    () => new Map(raw.map((item) => [String(item.id ?? ""), String(item.name ?? "")])),
    [raw],
  );

  const rows = useMemo<DepartmentRow[]>(
    () =>
      raw.map((item) => ({
        id: String(item.id ?? ""),
        code: String(item.code ?? ""),
        name: String(item.name ?? ""),
        parent: item.parent_id ? (names.get(String(item.parent_id)) ?? "—") : "顶级",
        sort_order: String(item.sort_order ?? "0"),
        users: String(item.user_count ?? "—"),
      })),
    [names, raw],
  );

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter(
      (row) => row.name.toLowerCase().includes(needle) || row.code.toLowerCase().includes(needle),
    );
  }, [rows, search]);

  const handleCreate = async () => {
    setFormError(null);
    if (!form.code.trim() || !form.name.trim()) {
      setFormError("请填写部门编码与名称");
      return;
    }
    const sortOrder = Number(form.sort_order);
    if (!Number.isFinite(sortOrder)) {
      setFormError("排序必须是数字");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: form.code.trim(),
        name: form.name.trim(),
        parent_id: form.parent_id || undefined,
        sort_order: sortOrder,
        description: form.description.trim() || undefined,
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
        title="部门管理"
        subtitle="部门决定部门数据范围的可见边界：部门范围的用户只能看到本部门创建的单据"
        actions={<WorkspaceToolbarButton onClick={() => setShowCreate(true)}>新建部门</WorkspaceToolbarButton>}
      />

      {showCreate ? (
        <div className="rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <h3 className="mb-3 text-sm font-semibold">新建部门</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label className="text-xs">
              <span className="mb-1 block text-[var(--color-text-muted)]">部门编码 *</span>
              <input
                className={fieldInputClass}
                value={form.code}
                placeholder="如 prod"
                onChange={(e) => setForm((prev) => ({ ...prev, code: e.target.value }))}
              />
            </label>
            <label className="text-xs">
              <span className="mb-1 block text-[var(--color-text-muted)]">部门名称 *</span>
              <input
                className={fieldInputClass}
                value={form.name}
                placeholder="如 生产部"
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              />
            </label>
            <label className="text-xs">
              <span className="mb-1 block text-[var(--color-text-muted)]">上级部门</span>
              <select
                className={fieldInputClass}
                value={form.parent_id}
                onChange={(e) => setForm((prev) => ({ ...prev, parent_id: e.target.value }))}
              >
                <option value="">（顶级部门）</option>
                {raw.map((item) => (
                  <option key={String(item.id)} value={String(item.id)}>
                    {String(item.name ?? "")}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs">
              <span className="mb-1 block text-[var(--color-text-muted)]">排序</span>
              <input
                className={fieldInputClass}
                value={form.sort_order}
                onChange={(e) => setForm((prev) => ({ ...prev, sort_order: e.target.value }))}
              />
            </label>
          </div>
          {formError ? <p className="mt-2 text-xs text-[var(--color-danger)]">{formError}</p> : null}
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              className="btn-primary h-8 px-3 text-xs"
              disabled={createMutation.isPending}
              onClick={() => void handleCreate()}
            >
              {createMutation.isPending ? "提交中…" : "提交"}
            </button>
            <button
              type="button"
              className="h-8 rounded-[var(--radius-btn)] border border-[var(--color-border)] px-3 text-xs"
              onClick={() => {
                setShowCreate(false);
                setFormError(null);
              }}
            >
              取消
            </button>
          </div>
        </div>
      ) : null}

      <MasterListPage<DepartmentRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="部门管理"
        persistenceKey="platform-departments-v1"
        exportFilename="departments"
        columns={[
          { key: "code", title: "编码", canView: true, width: 120 },
          { key: "name", title: "名称", canView: true, width: 160 },
          { key: "parent", title: "上级部门", canView: true, width: 140 },
          { key: "sort_order", title: "排序", canView: true, width: 80 },
        ]}
        rows={filtered}
        total={filtered.length}
        page={1}
        onPageChange={() => undefined}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
        emptyHint="创建部门后即可为用户的部门数据范围建立边界"
      />
    </IndustrialPage>
  );
}
