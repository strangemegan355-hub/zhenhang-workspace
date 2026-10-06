"use client";

import * as React from "react";
import { computeFields, computePricingViaFormulas } from "@zhenhang/quote-runtime";
import type { QuoteLineRow } from "./types";

const DEFAULT_FORMULAS: Record<string, string> = {
  line_cost: "base_cost",
  margin_amount: "line_cost * margin_rate",
  revenue: "line_cost + margin_amount",
  profit: "revenue - line_cost",
};

export function FormulaLivePanel({
  lines,
  marginRate,
  discountRate = 0,
}: {
  lines: QuoteLineRow[];
  marginRate: number;
  discountRate?: number;
}) {
  const baseCost = lines.reduce((s, l) => s + l.quantity * (l.unit_cost ?? l.unit_price * 0.7), 0);
  const totalQty = Math.max(
    lines.reduce((s, l) => s + l.quantity, 0),
    1,
  );
  // The memo depends on scalars rather than on an object built during render: reading properties off a
  // fresh object is what stopped the React Compiler from preserving this memoization.
  const formulaResult = React.useMemo(
    () =>
      computePricingViaFormulas(DEFAULT_FORMULAS, {
        base_cost: baseCost,
        margin_rate: marginRate,
        discount_rate: discountRate,
        qty: totalQty,
      }),
    [baseCost, marginRate, discountRate, totalQty],
  );
  const classic = computeFields({
    lines: lines.map((l) => ({
      sku: l.item_code,
      qty: l.quantity,
      unitCost: l.unit_cost ?? l.unit_price * 0.7,
    })),
    marginRate,
    discountRate,
  });

  const rows = [
    { key: "物料成本", value: baseCost, formula: "Σ(qty × unit_cost)" },
    { key: "毛利率", value: marginRate * 100, formula: "margin_rate × 100%", suffix: "%" },
    { key: "毛利额", value: formulaResult.margin_amount ?? classic.profit, formula: "line_cost × margin_rate" },
    { key: "报价收入", value: formulaResult.revenue ?? classic.revenue, formula: "line_cost + margin_amount" },
    { key: "利润", value: formulaResult.profit ?? classic.profit, formula: "revenue - line_cost" },
  ];

  return (
    <div className="space-y-2 rounded border p-3 dark:border-zinc-700">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">公式实时计算</span>
        <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
          LIVE
        </span>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500">
            <th className="pb-1">指标</th>
            <th className="pb-1">公式</th>
            <th className="pb-1 text-right">结果</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className="border-t dark:border-zinc-800">
              <td className="py-2 font-medium">{r.key}</td>
              <td className="py-2 font-mono text-xs text-zinc-500">{r.formula}</td>
              <td className="py-2 text-right tabular-nums">
                {r.suffix ? `${r.value.toFixed(1)}${r.suffix}` : r.value.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
