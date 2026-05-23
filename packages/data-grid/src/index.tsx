import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";

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
  onPageChange: (page: number) => void;
  onExport?: () => void;
  persistenceKey?: string;
  rowKey?: (row: T, idx: number) => string;
  onBatchAction?: (selected: T[]) => void;
  onRowClick?: (row: T) => void;
};

export function DataGrid<T extends Record<string, unknown>>({
  columns,
  rows,
  page,
  total,
  onPageChange,
  onExport,
  persistenceKey,
  rowKey,
  onBatchAction,
  onRowClick,
}: Props<T>) {
  const [order, setOrder] = React.useState(columns.map((c) => c.key));
  const [selectedRows, setSelectedRows] = React.useState<Record<string, boolean>>({});
  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32,
    overscan: 8,
  });

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

  const visible = order
    .map((key) => columns.find((c) => c.key === key))
    .filter((c): c is GridColumn<T> => Boolean(c && c.canView !== false));

  const selected = rows.filter((row, idx) => selectedRows[(rowKey ? rowKey(row, idx) : String(idx))] === true);

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

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-end gap-2">
        {onBatchAction ? (
          <button
            type="button"
            className="rounded border border-[#334155] bg-[#1E293B] px-2 text-xs text-[#CBD5E1] hover:border-[#475569]"
            style={{ height: 32 }}
            onClick={() => onBatchAction(selected)}
          >
            Batch ({selected.length})
          </button>
        ) : null}
        {onExport ? (
          <button
            type="button"
            className="rounded border border-[#334155] bg-[#1E293B] px-2 text-xs text-[#CBD5E1] hover:border-[#475569]"
            style={{ height: 32 }}
            onClick={onExport}
          >
            Export
          </button>
        ) : null}
      </div>
      <div ref={parentRef} className="max-h-[480px] overflow-auto rounded border">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 z-20 bg-[#111827]">
            <tr className="border-b border-[#334155]">
              <th className="sticky left-0 z-30 h-8 w-10 bg-[#111827] px-2 py-1 text-xs text-[#94A3B8]">
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
                  className={`h-8 px-2 py-1 text-xs text-[#94A3B8] ${col.fixed === "left" ? "sticky left-10 z-30 bg-[#111827]" : ""}`}
                  style={{ width: col.width ?? 180 }}
                >
                  {col.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: "relative" }}>
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const idx = virtualRow.index;
              const row = rows[idx];
              const key = rowKey ? rowKey(row, idx) : String(idx);
              return (
                <tr
                  key={key}
                  className={`absolute left-0 right-0 border-b border-[#334155] text-sm text-[#CBD5E1] ${onRowClick ? "cursor-pointer hover:bg-[#1a2332]" : ""}`}
                  style={{ transform: `translateY(${virtualRow.start}px)`, height: 32 }}
                  onClick={() => onRowClick?.(row)}
                >
                  <td className="sticky left-0 z-10 h-8 w-10 bg-[#0F172A] px-2 py-1">
                    <input
                      type="checkbox"
                      checked={selectedRows[key] === true}
                      onChange={(e) => setSelectedRows((s) => ({ ...s, [key]: e.target.checked }))}
                    />
                  </td>
                {visible.map((col) => (
                    <td
                      key={col.key}
                      className={`h-8 px-2 py-1 ${col.fixed === "left" ? "sticky left-10 z-10 bg-[#0F172A]" : ""}`}
                    >
                    {String(row[col.key] ?? "")}
                  </td>
                ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-end gap-2">
        <button onClick={() => onPageChange(Math.max(1, page - 1))}>Prev</button>
        <span>
          Page {page} / {Math.max(1, Math.ceil(total / 20))}
        </span>
        <button onClick={() => onPageChange(page + 1)}>Next</button>
      </div>
    </div>
  );
}
