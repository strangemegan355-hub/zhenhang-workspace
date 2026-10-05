"use client";

import {
  useCreateProductCategoryMutation,
  useDeleteProductCategoryMutation,
} from "@zhenhang/query-hooks";
import { WorkspaceToolbarButton } from "@zhenhang/ui";
import { confirmAndDelete } from "@/components/master/master-row-actions";
import { autoMasterCode } from "@/lib/auto-master-code";
import { fieldInputClass, fieldLabelClass, formPanelClass } from "@/lib/form-styles";
import { ChevronDown, ChevronRight, FolderTree } from "lucide-react";
import { useMemo, useState } from "react";

export type ProductCategoryItem = {
  id: string;
  code: string;
  name: string;
  parent_id: string | null;
};

type TreeNode = ProductCategoryItem & { children: TreeNode[] };

function buildTree(items: ProductCategoryItem[]): TreeNode[] {
  const map = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];
  for (const item of items) {
    map.set(item.id, { ...item, children: [] });
  }
  for (const node of map.values()) {
    if (node.parent_id && map.has(node.parent_id)) {
      map.get(node.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
    nodes.forEach((n) => sortNodes(n.children));
  };
  sortNodes(roots);
  return roots;
}

const defaultCatForm = { name: "", remark: "" };

export function ProductCategoryTree({
  categories,
  selectedId,
  onSelect,
  onChanged,
  loading,
}: {
  categories: ProductCategoryItem[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onChanged: () => void;
  loading?: boolean;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(defaultCatForm);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useCreateProductCategoryMutation();
  const deleteMutation = useDeleteProductCategoryMutation();

  const tree = useMemo(() => buildTree(categories), [categories]);
  const selectedCategory = categories.find((c) => c.id === selectedId) ?? null;

  const toggleExpand = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCreate = async () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("请填写分类名称");
      return;
    }
    try {
      await createMutation.mutateAsync({
        code: autoMasterCode(form.name.trim(), "CAT"),
        name: form.name.trim(),
        parent_id: selectedId || undefined,
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultCatForm);
      setShowCreate(false);
      onChanged();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleDeleteSelected = async () => {
    if (!selectedCategory) return;
    const ok = await confirmAndDelete(selectedCategory.name, () => deleteMutation.mutateAsync(selectedCategory.id));
    if (ok) {
      onSelect(null);
      onChanged();
    }
  };

  const renderNode = (node: TreeNode, depth = 0) => {
    const hasChildren = node.children.length > 0;
    const isExpanded = expanded[node.id] !== false;
    const isActive = selectedId === node.id;

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-1 rounded px-1 py-1 text-sm transition-colors ${
            isActive
              ? "bg-[var(--color-primary-soft)] font-medium text-[var(--color-text)]"
              : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)] hover:text-[var(--color-text)]"
          }`}
          style={{ paddingLeft: `${depth * 12 + 4}px` }}
        >
          {hasChildren ? (
            <button
              type="button"
              className="shrink-0 rounded p-0.5 hover:bg-[var(--color-border-soft)]"
              onClick={() => toggleExpand(node.id)}
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : (
            <span className="inline-block w-5 shrink-0" />
          )}
          <button
            type="button"
            className="min-w-0 flex-1 truncate text-left"
            title={`${node.name}`}
            onClick={() => onSelect(node.id)}
          >
            {node.name}
          </button>
        </div>
        {hasChildren && isExpanded ? node.children.map((child) => renderNode(child, depth + 1)) : null}
      </div>
    );
  };

  return (
    <div className="flex h-full min-h-0 flex-col rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="flex items-center justify-between gap-2 border-b border-[var(--color-border)] px-3 py-2">
        <div className="flex items-center gap-1.5 text-sm font-semibold text-[var(--color-text)]">
          <FolderTree size={16} className="text-[var(--color-text-muted)]" />
          产品分类
        </div>
        <WorkspaceToolbarButton compact onClick={() => setShowCreate((v) => !v)}>
          新建
        </WorkspaceToolbarButton>
      </div>

      {showCreate ? (
        <div className={`mx-2 mt-2 ${formPanelClass}`}>
          <div className="mb-2 space-y-2">
            {selectedCategory ? (
              <p className="text-xs text-[var(--color-text-muted)]">
                上级分类：{selectedCategory.name}
              </p>
            ) : (
              <p className="text-xs text-[var(--color-text-muted)]">将作为顶级分类</p>
            )}
            <label className="block space-y-1">
              <span className={fieldLabelClass}>分类名称 *</span>
              <input
                className={fieldInputClass}
                value={form.name}
                onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
                placeholder="如 泵类"
              />
            </label>
          </div>
          {formError ? <p className="mb-2 text-sm text-[var(--color-danger)]">{formError}</p> : null}
          <div className="flex justify-end gap-2">
            <WorkspaceToolbarButton compact onClick={() => setShowCreate(false)}>
              取消
            </WorkspaceToolbarButton>
            <WorkspaceToolbarButton compact onClick={() => void handleCreate()} loading={createMutation.isPending}>
              保存
            </WorkspaceToolbarButton>
          </div>
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-auto p-2">
        <button
          type="button"
          className={`mb-1 w-full rounded px-2 py-1.5 text-left text-sm transition-colors ${
            selectedId === null
              ? "bg-[var(--color-primary-soft)] font-medium text-[var(--color-text)]"
              : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)]"
          }`}
          onClick={() => onSelect(null)}
        >
          全部产品
        </button>
        {loading ? (
          <p className="px-2 py-3 text-sm text-[var(--color-text-muted)]">加载分类…</p>
        ) : tree.length === 0 ? (
          <p className="px-2 py-3 text-sm text-[var(--color-text-muted)]">暂无分类，点击「新建」添加</p>
        ) : (
          tree.map((node) => renderNode(node))
        )}
      </div>

      {selectedCategory ? (
        <div className="border-t border-[var(--color-border)] p-2">
          <WorkspaceToolbarButton variant="danger" className="w-full" onClick={() => void handleDeleteSelected()}>
            删除当前分类
          </WorkspaceToolbarButton>
        </div>
      ) : null}
    </div>
  );
}
