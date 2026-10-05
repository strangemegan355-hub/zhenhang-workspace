"use client";

import { useState, useMemo } from "react";
import { apiClient } from "@zhenhang/http-client";
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

export default function OptionGroupsSection({
  machineOptions,
}: {
  machineOptions: Array<{ value: string; label: string }>;
}) {
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [groups, setGroups] = useState<GroupRow[]>([]);
  const [items, setItems] = useState<ItemRow[]>([]);
  const [loading, setLoading] = useState(false);
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

  const [submitting, setSubmitting] = useState(false);

  async function loadGroups(machineId: string) {
    setLoading(true);
    try {
      const { data: resp } = await apiClient.get<{ data: Array<Record<string, unknown>> }>(
        `/api/v1/machines/${machineId}/option-groups`
      );
      const groupsData: any[] = resp.data ?? [];
      const rows: GroupRow[] = groupsData.map((g: any) => ({
        id: String(g.id ?? ""),
        name: String(g.name ?? ""),
        sortOrder: Number(g.sort_order ?? 0),
        itemCount: Array.isArray(g.items) ? g.items.length : 0,
      }));
      setGroups(rows);
      // Load items for all groups
      const allItems: ItemRow[] = [];
      for (const g of groupsData) {
        for (const i of (Array.isArray((g as any).items) ? (g as any).items : [])) {
          allItems.push({
            id: String((i as any).id ?? ""),
            name: String((i as any).name ?? ""),
            priceAdjustment: Number((i as any).price_adjustment ?? 0),
            sortOrder: Number((i as any).sort_order ?? 0),
            groupId: String(g.id ?? ""),
          });
        }
      }
      setItems(allItems);
    } catch {
      setGroups([]);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleMachineChange(id: string) {
    setSelectedMachineId(id);
    setSelectedGroupId("");
    setSelectedGroupLabel("");
    closeAllForms();
    if (id) await loadGroups(id);
    else {
      setGroups([]);
      setItems([]);
    }
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
    setSubmitting(true);
    const body = {
      name: groupForm.name.trim(),
      sort_order: Number(groupForm.sort_order) || 0,
    };
    try {
      if (groupEditId) {
        await apiClient.put(`/api/v1/option-groups/${groupEditId}`, body);
      } else {
        await apiClient.post(`/api/v1/machines/${selectedMachineId}/option-groups`, body);
      }
      closeAllForms();
      await loadGroups(selectedMachineId);
    } catch (err: any) {
      setGroupError(err?.response?.data?.detail?.detail ?? err?.message ?? "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteGroup(id: string, label: string) {
    if (!window.confirm(`确认删除选配组「${label}」及其中所有选项？`)) return;
    try {
      await apiClient.delete(`/api/v1/option-groups/${id}`);
      if (selectedGroupId === id) {
        setSelectedGroupId("");
        setSelectedGroupLabel("");
      }
      await loadGroups(selectedMachineId);
    } catch (err: any) {
      window.alert(err?.response?.data?.detail?.detail ?? err?.message ?? "删除失败");
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
    setSubmitting(true);
    const body = {
      name: itemForm.name.trim(),
      price_adjustment: Number(itemForm.price_adjustment) || 0,
      sort_order: Number(itemForm.sort_order) || 0,
    };
    try {
      if (itemEditId) {
        await apiClient.put(`/api/v1/option-items/${itemEditId}`, body);
      } else {
        await apiClient.post(`/api/v1/option-groups/${selectedGroupId}/items`, body);
      }
      closeAllForms();
      await loadGroups(selectedMachineId);
    } catch (err: any) {
      setItemError(err?.response?.data?.detail?.detail ?? err?.message ?? "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteItem(id: string, label: string) {
    if (!window.confirm(`确认删除选项「${label}」？`)) return;
    try {
      await apiClient.delete(`/api/v1/option-items/${id}`);
      await loadGroups(selectedMachineId);
    } catch (err: any) {
      window.alert(err?.response?.data?.detail?.detail ?? err?.message ?? "删除失败");
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
        query={{ isLoading: loading, isError: false, refetch: () => { if (selectedMachineId) loadGroups(selectedMachineId); } } as any}
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
                if (!selectedMachineId) { window.alert("请先选择机型"); return; }
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
        query={{ isLoading: loading, isError: false, refetch: () => { if (selectedMachineId) loadGroups(selectedMachineId); } } as any}
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
                if (!selectedMachineId) { window.alert("请先选择机型"); return; }
                if (!selectedGroupId) { window.alert("请先在选配组列表选择一个组"); return; }
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
