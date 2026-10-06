"use client";

import { useToastStore } from "@zhenhang/realtime";

import { dangerActionClass, linkActionClass } from "@/lib/form-styles";

export function MasterRowActions({
  onDelete,
  onEdit,
  deleteLabel = "删除",
  editLabel = "修改",
}: {
  onDelete: () => void;
  onEdit?: () => void;
  deleteLabel?: string;
  editLabel?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      {onEdit ? (
        <button type="button" className={linkActionClass} onClick={onEdit}>
          {editLabel}
        </button>
      ) : null}
      <button type="button" className={dangerActionClass} onClick={onDelete}>
        {deleteLabel}
      </button>
    </div>
  );
}

export async function confirmAndDeleteSelected(
  items: Array<{ id: string; label: string }>,
  deleteFn: (id: string) => Promise<unknown>,
): Promise<number> {
  if (items.length === 0) {
    notify("请先勾选要删除的记录");
    return 0;
  }
  const preview = items
    .slice(0, 3)
    .map((item) => item.label)
    .join("、");
  const suffix = items.length > 3 ? ` 等 ${items.length} 项` : "";
  if (!window.confirm(`确认删除选中的 ${items.length} 项？\n${preview}${suffix}`)) return 0;

  let deleted = 0;
  for (const item of items) {
    try {
      await deleteFn(item.id);
      deleted += 1;
    } catch (err) {
      notify(`删除「${item.label}」失败：${err instanceof Error ? err.message : "未知错误"}`);
      break;
    }
  }
  return deleted;
}

export function rowDeleteItems<T extends { id?: string; code?: string; name?: string }>(rows: T[]) {
  return rows.map((row) => ({
    id: String(row.id ?? ""),
    label: String(row.name || row.code || row.id || "未命名"),
  }));
}

export async function confirmAndDelete(label: string, deleteFn: () => Promise<unknown>): Promise<boolean> {
  if (!window.confirm(`确认删除「${label}」？`)) return false;
  try {
    await deleteFn();
    return true;
  } catch (err) {
    notify(err instanceof Error ? err.message : "删除失败");
    return false;
  }
}

export async function batchDeleteRows<T extends { id?: string; code?: string; name?: string }>(
  rows: T[],
  deleteFn: (id: string) => Promise<unknown>,
  refetch?: () => void,
): Promise<number> {
  const deleted = await confirmAndDeleteSelected(rowDeleteItems(rows), deleteFn);
  if (deleted > 0) refetch?.();
  return deleted;
}

function notify(title: string) {
  useToastStore.getState().push({ title });
}
