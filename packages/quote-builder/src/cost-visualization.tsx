"use client";

import * as React from "react";
import { computeFields } from "@zhenhang/quote-runtime";
import type { CostBreakdownSlice, QuoteLineRow } from "./types";

function buildSlices(lines: QuoteLineRow[]): CostBreakdownSlice[] {
  const palette = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4"];
  const groups = new Map<string, number>();
  for (const line of lines) {
    const prefix = line.item_code.split("-")[0] || line.item_code.slice(0, 2) || "其他";
    const cost = line.quantity * (line.unit_cost ?? line.unit_price * 0.7);
    groups.set(prefix, (groups.get(prefix) ?? 0) + cost);
  }
  if (!groups.size) {
    return [{ label: "暂无数据", value: 1, color: "#94a3b8" }];
  }
  return [...groups.entries()].map(([label, value], i) => ({
    label,
    value,
    color: palette[i % palette.length],
  }));
}

export function CostVisualization({
  lines,
  marginRate,
  revenue,
  profit,
}: {
  lines: QuoteLineRow[];
  marginRate: number;
  revenue?: number;
  profit?: number;
}) {
  const computed = computeFields({
    lines: lines.map((l) => ({
      sku: l.item_code,
      qty: l.quantity,
      unitCost: l.unit_cost ?? l.unit_price * 0.7,
    })),
    marginRate,
  });
  const slices = buildSlices(lines);
  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const rev = revenue ?? computed.revenue;
  const prof = profit ?? computed.profit;
  const marginPct = rev > 0 ? (prof / rev) * 100 : 0;

  return (
    <div className="space-y-3 rounded border p-3 dark:border-zinc-700">
      <div className="text-sm font-semibold">成本与利润可视化</div>
      <div className="grid grid-cols-3 gap-2">
        <KpiCard label="总成本" value={computed.totalCost} tone="blue" />
        <KpiCard label="报价收入" value={rev} tone="emerald" />
        <KpiCard label="毛利率" value={marginPct} suffix="%" tone="amber" />
      </div>
      <div>
        <div className="mb-1 text-xs text-zinc-500">成本结构</div>
        <div className="flex h-6 overflow-hidden rounded-full">
          {slices.map((s) => (
            <div
              key={s.label}
              title={`${s.label}: ${s.value.toFixed(0)}`}
              style={{ width: `${(s.value / total) * 100}%`, backgroundColor: s.color }}
            />
          ))}
        </div>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {slices.map((s) => (
            <span key={s.label} className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              {s.label} ({((s.value / total) * 100).toFixed(0)}%)
            </span>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded border p-2 dark:border-zinc-700">
          <div className="text-zinc-500">利润额</div>
          <div className="text-lg font-semibold tabular-nums">{prof.toFixed(2)}</div>
        </div>
        <div className="rounded border p-2 dark:border-zinc-700">
          <div className="text-zinc-500">行项目数</div>
          <div className="text-lg font-semibold">{lines.length}</div>
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  suffix,
  tone,
}: {
  label: string;
  value: number;
  suffix?: string;
  tone: "blue" | "emerald" | "amber";
}) {
  const bg =
    tone === "blue"
      ? "bg-blue-50 dark:bg-blue-950/50"
      : tone === "emerald"
        ? "bg-emerald-50 dark:bg-emerald-950/50"
        : "bg-amber-50 dark:bg-amber-950/50";
  return (
    <div className={`rounded border p-2 ${bg} dark:border-zinc-700`}>
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-lg font-bold tabular-nums">
        {value.toFixed(suffix ? 1 : 2)}
        {suffix ?? ""}
      </div>
    </div>
  );
}
