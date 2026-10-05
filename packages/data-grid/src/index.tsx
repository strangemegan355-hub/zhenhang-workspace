import * as React from "react";
import type { CSSProperties, ReactNode } from "react";

export type GridColumn<T> = {
  key: keyof T & string;
  title: string;
  canView?: boolean;
  fixed?: "left";
  width?: number;
};

type Props<T extends Record<string, unknown>> = {
  columns: Array<GridColumn<T>>;
  rows: T[];
  page: number;
  total: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  onExport?: () => void;
  persistenceKey?: string;
  rowKey?: (row: T, idx: number) => string;
  onBatchAction?: (selected: T[]) => void;
  batchActionLabel?: string;
  hideBatchToolbar?: boolean;
  onSelectionChange?: (selected: T[]) => void;
  onRowClick?: (row: T) => void;
  rowActions?: (row: T) => ReactNode;
  emptyMessage?: string;
};

const CHECKBOX_COL_WIDTH = 40;
const ACTIONS_COL_WIDTH = 112;
const DEFAULT_COL_WIDTH = 160;

function colWidth(width?: number) {
  return width ?? DEFAULT_COL_WIDTH;
}

function cellStyle(width?: number): CSSProperties {
  const w = colWidth(width);
  return { width: w, minWidth: w, maxWidth: w };
}

function fixedColStyle(width?: number): CSSProperties {
  return { ...cellStyle(width), left: CHECKBOX_COL_WIDTH };
}

export function DataGrid<T extends Record<string, unknown>>({
  columns,
  rows,
  page,
  total,
  pageSize = 20,
  onPageChange,
  onExport,
  persistenceKey,
  rowKey,
  onBatchAction,
  batchActionLabel = "删除选中",
  hideBatchToolbar = false,
  onSelectionChange,
  onRowClick,
  rowActions,
  emptyMessage = "暂无数据",
}: Props<T>) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const [order, setOrder] = React.useState(columns.map((c) => c.key));
  const [selectedRows, setSelectedRows] = React.useState<Record<string, boolean>>({});
  const parentRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!persistenceKey) return;
    const raw = localStorage.getItem(`grid-column-order:${persistenceKey}`);
    if (!raw) return;
    const saved = JSON.parse(raw) as string[];
    if (Array.isArray(saved) && saved.length) setOrder(saved as Array<keyof T & string>);
  }, [persistenceKey]);

  React.useEffect(() => {
    if (!persistenceKey) return;
    localStorage.setItem(`grid-column-order:${persistenceKey}`, JSON.stringify(order));
  }, [order, persistenceKey]);

  React.useEffect(() => {
    setOrder(columns.map((c) => c.key));
  }, [columns]);

  const visible = order
    .map((key) => columns.find((c) => c.key === key))
    .filter((c): c is GridColumn<T> => Boolean(c && c.canView !== false));

  const selected = rows.filter((row, idx) => selectedRows[(rowKey ? rowKey(row, idx) : String(idx))] === true);

  React.useEffect(() => {
    setSelectedRows({});
  }, [rows]);

  React.useEffect(() => {
    if (!onSelectionChange) return;
    const next = rows.filter((row, idx) => selectedRows[(rowKey ? rowKey(row, idx) : String(idx))] === true);
    onSelectionChange(next);
  }, [selectedRows, rows, rowKey, onSelectionChange]);

  const dragStart = (key: string) => (e: React.DragEvent<HTMLTableHeaderCellElement>) => {
    e.dataTransfer.setData("text/plain", key);
  };
  const dragDrop = (target: string) => (e: React.DragEvent<HTMLTableHeaderCellElement>) => {
    e.preventDefault();
    const source = e.dataTransfer.getData("text/plain");
    if (!source || source === target) return;
    const next = [...order];
    const sourceIdx = next.indexOf(source as keyof T & string);
    const targetIdx = next.indexOf(target as keyof T & string);
    if (sourceIdx < 0 || targetIdx < 0) return;
    next.splice(sourceIdx, 1);
    next.splice(targetIdx, 0, source as keyof T & string);
    setOrder(next);
  };

  const tableMinWidth =
    CHECKBOX_COL_WIDTH +
    visible.reduce((sum, col) => sum + colWidth(col.width), 0) +
    (rowActions ? ACTIONS_COL_WIDTH : 0);

  const hasToolbarActions = !hideBatchToolbar && Boolean(onBatchAction || onExport);

  return (
    <div className="flex min-h-[240px] flex-1 flex-col gap-2">
      {hasToolbarActions ? (
        <div className="flex shrink-0 items-center justify-end gap-2">
          {onBatchAction ? (
            <button
              type="button"
              className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-danger)] transition-colors hover:bg-[var(--color-accent-soft)] disabled:cursor-not-allowed disabled:opacity-40"
              style={{ height: 36 }}
              disabled={selected.length === 0}
              onClick={() => onBatchAction(selected)}
            >
              {batchActionLabel}
              {selected.length > 0 ? ` (${selected.length})` : ""}
            </button>
          ) : null}
          {onExport ? (
            <button
              type="button"
              className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-soft)]"
              style={{ height: 36 }}
              onClick={onExport}
            >
              导出
            </button>
          ) : null}
        </div>
      ) : null}
      <div className="min-h-0 flex-1">
        {rows.length === 0 ? (
          <div className="rounded border border-dashed border-[var(--color-border)] px-4 py-10 text-center text-sm text-[var(--color-text-muted)]">
            {emptyMessage}
          </div>
        ) : (
          <div
            ref={parentRef}
            className="h-full min-h-0 flex-1 overflow-auto rounded border border-[var(--color-border)] bg-[var(--color-surface)]"
          >
            <table className="w-full table-fixed border-collapse text-left text-sm" style={{ minWidth: tableMinWidth }}>
              <colgroup>
                <col style={{ width: CHECKBOX_COL_WIDTH }} />
                {visible.map((col) => (
                  <col key={col.key} style={cellStyle(col.width)} />
                ))}
                {rowActions ? <col style={{ width: ACTIONS_COL_WIDTH }} /> : null}
              </colgroup>
              <thead className="sticky top-0 z-20 bg-[var(--color-surface-soft)]">
                <tr className="border-b border-[var(--color-border)]">
                  <th
                    className="sticky left-0 z-40 h-9 bg-[var(--color-surface-soft)] px-2 py-1 text-sm text-[var(--color-text-muted)]"
                    style={cellStyle(CHECKBOX_COL_WIDTH)}
                  >
                    <input
                      type="checkbox"
                      checked={selected.length > 0 && selected.length === rows.length}
                      onChange={(e) =>
                        setSelectedRows(
                          e.target.checked
                            ? Object.fromEntries(rows.map((row, idx) => [rowKey ? rowKey(row, idx) : String(idx), true]))
                            : {},
                        )
                      }
                    />
                  </th>
                  {visible.map((col) => (
                    <th
                      key={col.key}
                      draggable
                      onDragStart={dragStart(col.key)}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={dragDrop(col.key)}
                      className={`h-9 truncate px-2 py-1 text-sm font-medium text-[var(--color-text-muted)] ${col.fixed === "left" ? "sticky z-30 bg-[var(--color-surface-soft)]" : ""}`}
                      style={col.fixed === "left" ? fixedColStyle(col.width) : cellStyle(col.width)}
                      title={col.title}
                    >
                      {col.title}
                    </th>
                  ))}
                  {rowActions ? (
                    <th
                      className="sticky right-0 z-30 h-9 bg-[var(--color-surface-soft)] px-2 py-1 text-sm text-[var(--color-text-muted)]"
                      style={cellStyle(ACTIONS_COL_WIDTH)}
                    >
                      操作
                    </th>
                  ) : null}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => {
                  const key = rowKey ? rowKey(row, idx) : String(idx);
                  return (
                    <tr
                      key={key}
                      className={`border-b border-[var(--color-border-soft)] text-sm text-[var(--color-text)] ${onRowClick ? "cursor-pointer hover:bg-[var(--color-surface-soft)]" : ""}`}
                      onClick={() => onRowClick?.(row)}
                    >
                      <td
                        className="sticky left-0 z-20 h-9 bg-[var(--color-surface)] px-2 py-1"
                        style={cellStyle(CHECKBOX_COL_WIDTH)}
                      >
                        <input
                          type="checkbox"
                          checked={selectedRows[key] === true}
                          onChange={(e) => setSelectedRows((s) => ({ ...s, [key]: e.target.checked }))}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      {visible.map((col) => (
                        <td
                          key={col.key}
                          className={`h-9 truncate px-2 py-1 ${col.fixed === "left" ? "sticky z-10 bg-[var(--color-surface)]" : ""}`}
                          style={col.fixed === "left" ? fixedColStyle(col.width) : cellStyle(col.width)}
                          title={String(row[col.key] ?? "")}
                        >
                          {String(row[col.key] ?? "")}
                        </td>
                      ))}
                      {rowActions ? (
                        <td
                          className="sticky right-0 z-10 h-9 bg-[var(--color-surface)] px-2 py-1"
                          style={cellStyle(ACTIONS_COL_WIDTH)}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {rowActions(row)}
                        </td>
                      ) : null}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <footer className="mt-auto flex shrink-0 items-center justify-end gap-2 border-t border-[var(--color-border)] pt-2 text-sm text-[var(--color-text-muted)]">
        <button
          type="button"
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface-soft)] disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          上一页
        </button>
        <span>
          第 {page} / {pageCount} 页 · 共 {total} 条
        </span>
        <button
          type="button"
          className="rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-surface-soft)] disabled:opacity-40"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </button>
      </footer>
    </div>
  );
}
