"use client";

import { useToastStore } from "@zhenhang/realtime";

import {
  useCreateOptionGroupMutation,
  useCreateOptionItemMutation,
  useDeleteOptionGroupMutation,
  useDeleteOptionItemMutation,
  useOptionGroupsQuery,
  useUpdateOptionGroupMutation,
  useUpdateOptionItemMutation,
} from "@zhenhang/query-hooks";
import { apiErrorMessage } from "@/lib/api-error";

import { useState, useMemo } from "react";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { WorkspaceToolbarButton } from "@zhenhang/ui";
import { searchInputClass } from "@/lib/form-styles";

type GroupRow = { id: string; name: string; sortOrder: number; itemCount: number };
type ItemRow = { id: string; name: string; priceAdjustment: number; sortOrder: number; groupId: string };

function MachineSelect({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (id: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <select
      className={searchInputClass}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">请选择机型</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function groupItems(group: Record<string, unknown>): Array<Record<string, unknown>> {
  return Array.isArray(group.items) ? (group.items as Array<Record<string, unknown>>) : [];
}

export default function OptionGroupsSection({
  machineOptions,
}: {
  machineOptions: Array<{ value: string; label: string }>;
}) {
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedGroupLabel, setSelectedGroupLabel] = useState("");

  const [showGroupForm, setShowGroupForm] = useState(false);
  const [groupEditId, setGroupEditId] = useState<string | null>(null);
  const [groupForm, setGroupForm] = useState({ name: "", sort_order: "0" });
  const [groupError, setGroupError] = useState<string | null>(null);

  const [showItemForm, setShowItemForm] = useState(false);
  const [itemEditId, setItemEditId] = useState<string | null>(null);
  const [itemForm, setItemForm] = useState({ name: "", price_adjustment: "0", sort_order: "0" });
  const [itemError, setItemError] = useState<string | null>(null);

  // One query feeds both tables: the machine-options endpoint nests each group's items. The
  // hooks own caching and invalidation, which the previous hand-written loader did not.
  const groupsQuery = useOptionGroupsQuery(selectedMachineId || null);
  const createGroupMutation = useCreateOptionGroupMutation();
  const updateGroupMutation = useUpdateOptionGroupMutation();
  const deleteGroupMutation = useDeleteOptionGroupMutation();
  const createItemMutation = useCreateOptionItemMutation();
  const updateItemMutation = useUpdateOptionItemMutation();
  const deleteItemMutation = useDeleteOptionItemMutation();

  const groupsData = useMemo(() => groupsQuery.data ?? [], [groupsQuery.data]);

  const groups: GroupRow[] = useMemo(
    () =>
      groupsData.map((g) => ({
        id: String(g.id ?? ""),
        name: String(g.name ?? ""),
        sortOrder: Number(g.sort_order ?? 0),
        itemCount: groupItems(g as unknown as Record<string, unknown>).length,
      })),
    [groupsData]
  );

  const items: ItemRow[] = useMemo(() => {
    const allItems: ItemRow[] = [];
    for (const g of groupsData) {
      for (const i of groupItems(g as unknown as Record<string, unknown>)) {
        allItems.push({
          id: String(i.id ?? ""),
          name: String(i.name ?? ""),
          priceAdjustment: Number(i.price_adjustment ?? 0),
          sortOrder: Number(i.sort_order ?? 0),
          groupId: String(g.id ?? ""),
        });
      }
    }
    return allItems;
  }, [groupsData]);

  const loading = groupsQuery.isFetching;
  const submitting =
    createGroupMutation.isPending ||
    updateGroupMutation.isPending ||
    deleteGroupMutation.isPending ||
    createItemMutation.isPending ||
    updateItemMutation.isPending ||
    deleteItemMutation.isPending;

  const reload = () => {
    void groupsQuery.refetch();
  };

  function handleMachineChange(id: string) {
    setSelectedMachineId(id);
    setSelectedGroupId("");
    setSelectedGroupLabel("");
    closeAllForms();
  }

  function closeAllForms() {
    setShowGroupForm(false);
    setShowItemForm(false);
    setGroupEditId(null);
    setItemEditId(null);
    setGroupError(null);
    setItemError(null);
  }

  async function handleSaveGroup() {
    setGroupError(null);
    if (!groupForm.name.trim()) {
      setGroupError("请填写组名称");
      return;
    }
    try {
      const sortOrder = Number(groupForm.sort_order) || 0;
      if (groupEditId) {
        await updateGroupMutation.mutateAsync({
          groupId: groupEditId,
          name: groupForm.name.trim(),
          sortOrder,
        });
      } else {
        await createGroupMutation.mutateAsync({
          machineId: selectedMachineId,
          name: groupForm.name.trim(),
          sortOrder,
        });
      }
      closeAllForms();
      reload();
    } catch (err) {
      setGroupError(apiErrorMessage(err, "保存失败"));
    }
  }

  async function handleDeleteGroup(id: string, label: string) {
    if (!window.confirm(`确认删除选配组「${label}」及其中所有选项？`)) return;
    try {
      await deleteGroupMutation.mutateAsync(id);
      if (selectedGroupId === id) {
        setSelectedGroupId("");
        setSelectedGroupLabel("");
      }
      reload();
    } catch (err) {
      notify(apiErrorMessage(err, "删除失败"));
    }
  }

  async function handleSaveItem() {
    setItemError(null);
    if (!selectedGroupId) {
      setItemError("请先选择选项组");
      return;
    }
    if (!itemForm.name.trim()) {
      setItemError("请填写选项名称");
      return;
    }
    try {
      const priceAdjustment = Number(itemForm.price_adjustment) || 0;
      const sortOrder = Number(itemForm.sort_order) || 0;
      if (itemEditId) {
        await updateItemMutation.mutateAsync({
          itemId: itemEditId,
          name: itemForm.name.trim(),
          priceAdjustment,
          sortOrder,
        });
      } else {
        await createItemMutation.mutateAsync({
          groupId: selectedGroupId,
          name: itemForm.name.trim(),
          priceAdjustment,
          sortOrder,
        });
      }
      closeAllForms();
      reload();
    } catch (err) {
      setItemError(apiErrorMessage(err, "保存失败"));
    }
  }

  async function handleDeleteItem(id: string, label: string) {
    if (!window.confirm(`确认删除选项「${label}」？`)) return;
    try {
      await deleteItemMutation.mutateAsync(id);
      reload();
    } catch (err) {
      notify(apiErrorMessage(err, "删除失败"));
    }
  }

  const groupRows = useMemo(() => groups, [groups]);

  const filteredItems = useMemo(
    () => (selectedGroupId ? items.filter((i) => i.groupId === selectedGroupId) : []),
    [items, selectedGroupId]
  );

  return (
    <>
      {showGroupForm ? (
        <MasterCreateForm
          title={groupEditId ? "修改选配组" : "新增选配组"}
          fields={[
            { key: "name", label: "组名称", required: true, placeholder: "如 电机类型" },
            { key: "sort_order", label: "排序", type: "number", placeholder: "0" },
          ]}
          values={groupForm}
          onChange={(key, value) => setGroupForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveGroup()}
          onCancel={closeAllForms}
          submitting={submitting}
          error={groupError}
          submitLabel={groupEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {showItemForm ? (
        <MasterCreateForm
          title={itemEditId ? "修改选项" : "新增选项"}
          fields={[
            { key: "name", label: "选项名称", required: true, placeholder: "如 进口电机" },
            { key: "price_adjustment", label: "加价（元）", type: "number", placeholder: "如 5000" },
            { key: "sort_order", label: "排序", type: "number", placeholder: "0" },
          ]}
          values={itemForm}
          onChange={(key, value) => setItemForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveItem()}
          onCancel={closeAllForms}
          submitting={submitting}
          error={itemError}
          submitLabel={itemEditId ? "保存修改" : "保存"}
        />
      ) : null}

      <MasterListPage<GroupRow>
        embedded
        fill
        title="机型选配"
        persistenceKey="master-option-groups-v1"
        exportFilename="option-groups"
        columns={[
          { key: "name", title: "选配组", canView: true, fixed: "left", width: 150 },
          { key: "itemCount", title: "选项数", canView: true, width: 80 },
          { key: "sortOrder", title: "排序", canView: true, width: 60 },
        ]}
        rows={groupRows}
        total={groupRows.length}
        page={1}
        onPageChange={() => {}}
        search=""
        onSearchChange={() => {}}
        query={{
          isLoading: loading,
          isError: false,
          isFetching: loading,
          refetch: reload,
        }}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="text-xs text-emerald-400 hover:underline"
              onClick={() => { setSelectedGroupId(row.id); setSelectedGroupLabel(row.name); }}
            >
              选项
            </button>
            <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => {
              closeAllForms();
              setGroupEditId(row.id);
              setGroupForm({ name: row.name, sort_order: String(row.sortOrder) });
              setShowGroupForm(true);
            }}>
              修改
            </button>
            <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDeleteGroup(row.id, row.name)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <MachineSelect value={selectedMachineId} onChange={handleMachineChange} options={machineOptions} />
            <WorkspaceToolbarButton
              onClick={() => {
                if (!selectedMachineId) { notify("请先选择机型"); return; }
                closeAllForms();
                setGroupForm({ name: "", sort_order: "0" });
                setShowGroupForm(true);
              }}
              disabled={!selectedMachineId}
            >
              新增选配组
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={selectedMachineId ? "暂无选配组，请点击「新增选配组」添加" : "请先选择机型后再管理选配"}
      />

      <MasterListPage<ItemRow>
        embedded
        fill
        title="选项明细"
        persistenceKey="master-option-items-v1"
        exportFilename="option-items"
        columns={[
          { key: "name", title: "选项名称", canView: true, fixed: "left", width: 150 },
          { key: "priceAdjustment", title: "加价（元）", canView: true, width: 120 },
          { key: "sortOrder", title: "排序", canView: true, width: 60 },
        ]}
        rows={filteredItems}
        total={filteredItems.length}
        page={1}
        onPageChange={() => {}}
        search=""
        onSearchChange={() => {}}
        query={{
          isLoading: loading,
          isError: false,
          isFetching: loading,
          refetch: reload,
        }}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-2">
            <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => {
              closeAllForms();
              setItemEditId(row.id);
              setItemForm({ name: row.name, price_adjustment: String(row.priceAdjustment), sort_order: String(row.sortOrder) });
              setShowItemForm(true);
            }}>
              修改
            </button>
            <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDeleteItem(row.id, row.name)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">点选选配组中的「选项」按钮</span>
            <WorkspaceToolbarButton
              onClick={() => {
                if (!selectedMachineId) { notify("请先选择机型"); return; }
                if (!selectedGroupId) { notify("请先在选配组列表选择一个组"); return; }
                closeAllForms();
                setItemForm({ name: "", price_adjustment: "0", sort_order: "0" });
                setShowItemForm(true);
              }}
              disabled={!selectedGroupId}
            >
              新增选项
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={
          selectedGroupId
            ? `当前选配组：${selectedGroupLabel}，暂无选项，请点击「新增选项」添加`
            : "请先在上方选配组列表点击「选项」按钮选择要查看的组"
        }
      />
    </>
  );
}

function notify(title: string) {
  useToastStore.getState().push({ title });
}
