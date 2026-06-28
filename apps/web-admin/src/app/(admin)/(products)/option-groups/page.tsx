"use client";

import {
  useMachinesQuery,
  useOptionGroupsQuery,
  useCreateOptionGroupMutation,
  useDeleteOptionGroupMutation,
  useCreateOptionItemMutation,
  useDeleteOptionItemMutation,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import { fieldInputClass, fieldLabelClass, tableBodyRowClass, tableHeaderRowClass, dangerActionClass } from "@/lib/form-styles";

export default function OptionGroupsPage() {
  const [selectedMachineId, setSelectedMachineId] = useState<string>("");
  const [newGroupName, setNewGroupName] = useState("");
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null);
  const [newItemName, setNewItemName] = useState("");
  const [newItemPrice, setNewItemPrice] = useState("");
  const [error, setError] = useState<string | null>(null);

  const machinesQuery = useMachinesQuery(1);
  const groupsQuery = useOptionGroupsQuery(selectedMachineId || null);
  const createGroupMut = useCreateOptionGroupMutation();
  const deleteGroupMut = useDeleteOptionGroupMutation();
  const createItemMut = useCreateOptionItemMutation();
  const deleteItemMut = useDeleteOptionItemMutation();

  const machineOptions = useMemo(
    () =>
      ((machinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.machine_code ?? "")} ${String(m.name ?? "")}`,
      })),
    [machinesQuery.data],
  );

  const groups = (groupsQuery.data ?? []) as Array<{
    id: string; name: string; items?: Array<{ id: string; name: string; price_adjustment: number }>;
  }>;

  const handleCreateGroup = async () => {
    if (!newGroupName.trim() || !selectedMachineId) return;
    setError(null);
    try {
      await createGroupMut.mutateAsync({ machineId: selectedMachineId, name: newGroupName.trim() });
      setNewGroupName("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (!window.confirm("确认删除该选项组及其所有选项？")) return;
    await deleteGroupMut.mutateAsync(groupId);
  };

  const handleCreateItem = async (groupId: string) => {
    if (!newItemName.trim() || !newItemPrice) return;
    setError(null);
    try {
      await createItemMut.mutateAsync({
        groupId,
        name: newItemName.trim(),
        priceAdjustment: Number(newItemPrice),
      });
      setNewItemName("");
      setNewItemPrice("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "添加选项失败");
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!window.confirm("确认删除该选项？")) return;
    await deleteItemMut.mutateAsync(itemId);
  };

  return (
    <IndustrialPage gap="md" fill>
      <IndustrialPanel title="机型选项组管理">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>选择机型</span>
            <select
              className={fieldInputClass}
              value={selectedMachineId}
              onChange={(e) => { setSelectedMachineId(e.target.value); setExpandedGroupId(null); }}
            >
              <option value="">请选择机型...</option>
              {machineOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>

        {!selectedMachineId ? (
          <p className="text-sm text-[var(--color-text-muted)]">请先选择一个机型以管理其配置选项组</p>
        ) : groupsQuery.isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">加载中...</p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-end gap-2">
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>新建选项组</span>
                <input
                  className={fieldInputClass}
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  placeholder="如：颜色、材质、电机品牌"
                />
              </label>
              <WorkspaceToolbarButton onClick={() => void handleCreateGroup()} loading={createGroupMut.isPending}>
                创建
              </WorkspaceToolbarButton>
            </div>

            {error ? <p className="mb-2 text-xs text-red-500">{error}</p> : null}

            {groups.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)]">该机型暂无选项组</p>
            ) : (
              <div className="space-y-3">
                {groups.map((group) => (
                  <div key={group.id} className="rounded border border-zinc-200 p-3 dark:border-zinc-700">
                    <div className="flex items-center justify-between">
                      <button
                        type="button"
                        className="text-sm font-semibold"
                        onClick={() => setExpandedGroupId(expandedGroupId === group.id ? null : group.id)}
                      >
                        {expandedGroupId === group.id ? "▾" : "▸"} {group.name}
                      </button>
                      <button type="button" className={dangerActionClass} onClick={() => handleDeleteGroup(group.id)}>
                        删除组
                      </button>
                    </div>

                    {expandedGroupId === group.id ? (
                      <div className="mt-3 space-y-2 pl-4">
                        <div className="mb-2 flex flex-wrap items-end gap-2">
                          <label className="block space-y-1 text-xs">
                            <span className={fieldLabelClass}>选项名称</span>
                            <input className={fieldInputClass} value={newItemName} onChange={(e) => setNewItemName(e.target.value)} placeholder="如：ABB电机" />
                          </label>
                          <label className="block space-y-1 text-xs">
                            <span className={fieldLabelClass}>加价</span>
                            <input type="number" step={0.01} className={fieldInputClass} value={newItemPrice} onChange={(e) => setNewItemPrice(e.target.value)} placeholder="0" />
                          </label>
                          <WorkspaceToolbarButton onClick={() => void handleCreateItem(group.id)} loading={createItemMut.isPending}>
                            添加选项
                          </WorkspaceToolbarButton>
                        </div>

                        <table className="min-w-full text-xs">
                          <thead>
                            <tr className={tableHeaderRowClass}>
                              <th className="px-2 py-1 text-left font-normal">选项名称</th>
                              <th className="px-2 py-1 text-left font-normal">加价</th>
                              <th className="px-2 py-1 text-left font-normal">操作</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(group.items ?? []).map((item) => (
                              <tr key={item.id} className={tableBodyRowClass}>
                                <td className="px-2 py-1">{item.name}</td>
                                <td className="px-2 py-1 tabular-nums">+{Number(item.price_adjustment).toFixed(2)}</td>
                                <td className="px-2 py-1">
                                  <button type="button" className={dangerActionClass} onClick={() => handleDeleteItem(item.id)}>删除</button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
