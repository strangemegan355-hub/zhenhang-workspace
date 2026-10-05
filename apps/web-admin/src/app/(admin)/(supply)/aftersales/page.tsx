"use client";

import {
  useAftersalesQuery,
  useCreateAftersalesMutation,
  useUpdateAftersalesMutation,
  useDeleteAftersalesMutation,
  useCustomersQuery,
  useEquipmentUnitsQuery,
  type AftersalesCreatePayload,
  type AftersalesUpdatePayload,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import { dangerActionClass, fieldInputClass, fieldLabelClass, formPanelClass, tableBodyRowClass, tableHeaderRowClass } from "@/lib/form-styles";

const STATUS_LABEL: Record<string, string> = { draft: "草稿", confirmed: "已确认", in_progress: "处理中", completed: "已完成", cancelled: "已取消" };
const PRIORITY_LABEL: Record<string, string> = { low: "低", medium: "中", high: "高", urgent: "紧急" };
const PRIORITY_COLOR: Record<string, string> = { low: "text-[var(--color-text-muted)]", medium: "text-[var(--color-warning)]", high: "text-[var(--color-danger)]", urgent: "text-[var(--color-danger)] font-semibold" };

const emptyForm = { title: "", customer_id: "", equipment_unit_id: "", priority: "medium", description: "", assigned_to: "", scheduled_date: "" };

export default function AftersalesPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  const query = useAftersalesQuery(page, { status: statusFilter || undefined, priority: priorityFilter || undefined });
  const customersQuery = useCustomersQuery(1);
  const unitsQuery = useEquipmentUnitsQuery(1);
  const createMut = useCreateAftersalesMutation();
  const updateMut = useUpdateAftersalesMutation();
  const deleteMut = useDeleteAftersalesMutation();

  const customerOptions = useMemo(() => ((customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c: Record<string, unknown>) => ({ value: String(c.id ?? ""), label: String(c.name ?? "") })), [customersQuery.data]);
  const unitOptions = useMemo(() => ((unitsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((u: Record<string, unknown>) => ({ value: String(u.id ?? ""), label: String(u.serial_number ?? "") })), [unitsQuery.data]);

  const rows = useMemo(() => ((query.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((r: Record<string, unknown>) => ({
    id: String(r.id ?? ""), requestNo: String(r.request_no ?? ""), title: String(r.title ?? ""),
    customerName: String(r.customer_name ?? ""), status: String(r.status ?? ""),
    priority: String(r.priority ?? ""), equipmentSerial: String(r.equipment_serial ?? "-"),
    assigneeName: String(r.assignee_name ?? "-"), scheduledDate: String(r.scheduled_date ?? "").slice(0, 10),
    completedDate: String(r.completed_date ?? "").slice(0, 10),
  })), [query.data]);

  const total = (query.data as { total?: number } | undefined)?.total ?? rows.length;

  const handleSave = async () => {
    setError(null);
    if (!form.title.trim() || !form.customer_id) { setError("请填写标题和客户"); return; }
    try {
      if (editId) {
        const body: AftersalesUpdatePayload = { title: form.title.trim(), priority: form.priority, description: form.description.trim() || undefined, assigned_to: form.assigned_to || undefined, scheduled_date: form.scheduled_date || undefined };
        await updateMut.mutateAsync({ id: editId, body });
      } else {
        const body: AftersalesCreatePayload = { title: form.title.trim(), customer_id: form.customer_id, equipment_unit_id: form.equipment_unit_id || undefined, priority: form.priority, description: form.description.trim() || undefined, assigned_to: form.assigned_to || undefined, scheduled_date: form.scheduled_date || undefined };
        await createMut.mutateAsync(body);
      }
      setForm(emptyForm); setShowCreate(false); setEditId(null);
      void query.refetch();
    } catch (err) { setError(err instanceof Error ? err.message : "保存失败"); }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("确认删除？")) return;
    await deleteMut.mutateAsync(id);
    void query.refetch();
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    await updateMut.mutateAsync({ id, body: { status: newStatus } });
    void query.refetch();
  };

  return (
    <IndustrialPage gap="md" fill>
      <IndustrialPanel title="售后服务">
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>状态</span>
            <select className={fieldInputClass} value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
              <option value="">全部</option>
              {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>优先级</span>
            <select className={fieldInputClass} value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}>
              <option value="">全部</option>
              {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <WorkspaceToolbarButton onClick={() => { setShowCreate(true); setEditId(null); setForm(emptyForm); }}>新建工单</WorkspaceToolbarButton>
        </div>

        {error ? <p className="mb-2 text-xs text-red-500">{error}</p> : null}

        {showCreate ? (
          <div className={`${formPanelClass} mb-4 grid gap-3 md:grid-cols-2`}>
            <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>标题 *</span><input className={fieldInputClass} value={form.title} onChange={e => setForm(s => ({ ...s, title: e.target.value }))} /></label>
            <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>客户 *</span>
              <select className={fieldInputClass} value={form.customer_id} onChange={e => setForm(s => ({ ...s, customer_id: e.target.value }))}>
                <option value="">选择客户</option>
                {customerOptions.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>设备</span>
              <select className={fieldInputClass} value={form.equipment_unit_id} onChange={e => setForm(s => ({ ...s, equipment_unit_id: e.target.value }))}>
                <option value="">(可选)</option>
                {unitOptions.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>优先级</span>
              <select className={fieldInputClass} value={form.priority} onChange={e => setForm(s => ({ ...s, priority: e.target.value }))}>
                {Object.entries(PRIORITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
            <label className="block space-y-1 text-xs"><span className={fieldLabelClass}>计划日期</span><input type="date" className={fieldInputClass} value={form.scheduled_date} onChange={e => setForm(s => ({ ...s, scheduled_date: e.target.value }))} /></label>
            <label className="block space-y-1 text-xs md:col-span-2"><span className={fieldLabelClass}>描述</span><textarea className={fieldInputClass} value={form.description} onChange={e => setForm(s => ({ ...s, description: e.target.value }))} rows={3} /></label>
            <div className="flex justify-end gap-2 md:col-span-2">
              <WorkspaceToolbarButton onClick={() => { setShowCreate(false); setEditId(null); }}>取消</WorkspaceToolbarButton>
              <WorkspaceToolbarButton loading={createMut.isPending || updateMut.isPending} onClick={() => void handleSave()}>保存</WorkspaceToolbarButton>
            </div>
          </div>
        ) : null}

        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead><tr className={tableHeaderRowClass}>
              <th className="px-2 py-2 text-left font-normal">单号</th><th className="px-2 py-2 text-left font-normal">标题</th><th className="px-2 py-2 text-left font-normal">客户</th><th className="px-2 py-2 text-left font-normal">设备</th><th className="px-2 py-2 text-left font-normal">状态</th><th className="px-2 py-2 text-left font-normal">优先级</th><th className="px-2 py-2 text-left font-normal">负责人</th><th className="px-2 py-2 text-left font-normal">计划日</th><th className="px-2 py-2 text-left font-normal">操作</th>
            </tr></thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.id} className={tableBodyRowClass}>
                  <td className="px-2 py-2 font-mono text-[10px]">{row.requestNo}</td>
                  <td className="px-2 py-2">{row.title}</td>
                  <td className="px-2 py-2">{row.customerName}</td>
                  <td className="px-2 py-2 text-[var(--color-text-muted)]">{row.equipmentSerial}</td>
                  <td className="px-2 py-2">
                    <select className={fieldInputClass + " text-[10px]"} value={row.status} onChange={e => handleStatusChange(row.id, e.target.value)}>
                      {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </td>
                  <td className={`px-2 py-2 text-[10px] ${PRIORITY_COLOR[row.priority] ?? ""}`}>{PRIORITY_LABEL[row.priority] ?? row.priority}</td>
                  <td className="px-2 py-2 text-[var(--color-text-muted)]">{row.assigneeName}</td>
                  <td className="px-2 py-2">{row.scheduledDate || "-"}</td>
                  <td className="px-2 py-2">
                    <button type="button" className={dangerActionClass} onClick={() => handleDelete(row.id)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-[var(--color-text-muted)]">共 {total} 条</p>
      </IndustrialPanel>
    </IndustrialPage>
  );
}
