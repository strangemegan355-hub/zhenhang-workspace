"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import * as React from "react";
import { computeLineFormula, formatFormulaExpr } from "./inline-formula";
import { reorderArray } from "./tree-utils";
import type { QuoteLineRow } from "./types";

export function QuoteLineEditor({
  lines,
  onChange,
  onAdd,
  readOnly,
  marginRate = 0.2,
}: {
  lines: QuoteLineRow[];
  onChange: (lines: QuoteLineRow[]) => void;
  onAdd?: () => void;
  readOnly?: boolean;
  marginRate?: number;
}) {
  const [dragIdx, setDragIdx] = React.useState<number | null>(null);
  const parentRef = React.useRef<HTMLDivElement>(null);
  const useVirtual = lines.length > 24;

  const virtualizer = useVirtualizer({
    count: lines.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 6,
  });

  const update = (index: number, patch: Partial<QuoteLineRow>) => {
    onChange(lines.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };
  const remove = (index: number) => onChange(lines.filter((_, i) => i !== index));

  const renderRow = (row: QuoteLineRow, idx: number, style?: React.CSSProperties) => {
    const fx = computeLineFormula(row, marginRate);
    const subtotal = fx.lineTotal;
    return (
      <div
        key={`${row.item_code}-${idx}`}
        style={style}
        draggable={!readOnly}
        onDragStart={() => setDragIdx(idx)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={() => {
          if (dragIdx !== null && dragIdx !== idx) onChange(reorderArray(lines, dragIdx, idx));
          setDragIdx(null);
        }}
        className={`grid grid-cols-[20px_1fr_1fr_48px_64px_72px_88px_72px_24px] items-center gap-1 border-b border-zinc-100 px-2 py-1 text-sm dark:border-zinc-800 ${
          dragIdx === idx ? "opacity-50" : ""
        } hover:bg-zinc-50 dark:hover:bg-zinc-800/50`}
      >
        <span className="cursor-grab text-center text-zinc-400">{readOnly ? "" : "⠿"}</span>
        {readOnly ? (
          <span className="truncate font-mono text-xs">{row.item_code}</span>
        ) : (
          <input
            className="rounded border px-1 py-0.5 text-xs dark:border-zinc-600 dark:bg-zinc-900"
            value={row.item_code}
            onChange={(e) => update(idx, { item_code: e.target.value })}
          />
        )}
        {readOnly ? (
          <span className="truncate">{row.item_name}</span>
        ) : (
          <input
            className="rounded border px-1 py-0.5 text-xs dark:border-zinc-600 dark:bg-zinc-900"
            value={row.item_name}
            onChange={(e) => update(idx, { item_name: e.target.value })}
          />
        )}
        {readOnly ? (
          <span className="text-center text-xs">{row.unit}</span>
        ) : (
          <input
            className="rounded border px-1 py-0.5 text-center text-xs dark:border-zinc-600 dark:bg-zinc-900"
            value={row.unit}
            onChange={(e) => update(idx, { unit: e.target.value })}
          />
        )}
        {readOnly ? (
          <span className="text-right tabular-nums">{row.quantity}</span>
        ) : (
          <input
            type="number"
            className="rounded border px-1 py-0.5 text-right text-xs dark:border-zinc-600 dark:bg-zinc-900"
            value={row.quantity}
            onChange={(e) => update(idx, { quantity: Number(e.target.value) })}
          />
        )}
        {readOnly ? (
          <span className="text-right tabular-nums">{row.unit_price.toFixed(2)}</span>
        ) : (
          <input
            type="number"
            className="rounded border px-1 py-0.5 text-right text-xs dark:border-zinc-600 dark:bg-zinc-900"
            value={row.unit_price}
            onChange={(e) => update(idx, { unit_price: Number(e.target.value) })}
          />
        )}
        <div className="text-right">
          <div className="tabular-nums font-semibold">{subtotal.toFixed(2)}</div>
          <div className="font-mono text-[10px] text-zinc-500">{formatFormulaExpr(row)}</div>
        </div>
        <div className="text-right text-[10px] tabular-nums text-emerald-700 dark:text-emerald-400">
          +{fx.margin.toFixed(0)}
          <div className="text-zinc-500">{fx.marginPct.toFixed(0)}%</div>
        </div>
        {!readOnly ? (
          <button type="button" className="text-red-500 hover:text-red-700" onClick={() => remove(idx)}>
            ×
          </button>
        ) : (
          <span />
        )}
      </div>
    );
  };

  const total = lines.reduce((s, l) => s + l.quantity * l.unit_price, 0);

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800/80">
        <span className="text-sm font-semibold">报价行 · 行内公式</span>
        {!readOnly && onAdd ? (
          <button type="button" className="rounded-md border px-2 py-1 text-xs font-medium hover:bg-white dark:hover:bg-zinc-700" onClick={onAdd}>
            + 添加行
          </button>
        ) : null}
      </div>
      <div className="grid grid-cols-[20px_1fr_1fr_48px_64px_72px_88px_72px_24px] gap-1 border-b bg-zinc-100 px-2 py-1.5 text-[10px] font-semibold uppercase text-zinc-500 dark:bg-zinc-800">
        <span />
        <span>编码</span>
        <span>名称</span>
        <span className="text-center">单位</span>
        <span className="text-right">数量</span>
        <span className="text-right">单价</span>
        <span className="text-right">小计 / 公式</span>
        <span className="text-right">毛利</span>
        <span />
      </div>
      <div ref={parentRef} className={useVirtual ? "max-h-[300px] overflow-auto" : "max-h-[300px] overflow-auto"}>
        {useVirtual ? (
          <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
            {virtualizer.getVirtualItems().map((vi) => renderRow(lines[vi.index], vi.index, {
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${vi.size}px`,
              transform: `translateY(${vi.start}px)`,
            }))}
          </div>
        ) : (
          lines.map((row, idx) => renderRow(row, idx))
        )}
        {!lines.length ? (
          <p className="p-6 text-center text-xs text-zinc-500">从 BOM 导入或添加行项目</p>
        ) : null}
      </div>
      <div className="border-t border-zinc-200 bg-zinc-50 px-3 py-2 text-right dark:border-zinc-700 dark:bg-zinc-800">
        <span className="text-sm text-zinc-500">合计 </span>
        <span className="text-lg font-bold tabular-nums">¥{total.toLocaleString()}</span>
      </div>
    </div>
  );
}
