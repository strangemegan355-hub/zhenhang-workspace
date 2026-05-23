"use client";

import { computePricing } from "@zhenhang/quote-runtime";

export type DiffRow = {
  item: string;
  oldValue: number;
  newValue: number;
  changeType: "added" | "removed" | "changed";
};

function ChangeTag({ type }: { type: DiffRow["changeType"] }) {
  const cls =
    type === "added"
      ? "bg-green-100 text-green-700"
      : type === "removed"
        ? "bg-red-100 text-red-700"
        : "bg-amber-100 text-amber-700";
  return <span className={`rounded px-2 py-0.5 text-xs ${cls}`}>{type}</span>;
}

export function QuoteDiffPanel({
  fromVersion,
  toVersion,
  diffRows,
}: {
  fromVersion: string;
  toVersion: string;
  diffRows: DiffRow[];
}) {
  const costOld = diffRows.reduce((a, b) => a + b.oldValue, 0);
  const costNew = diffRows.reduce((a, b) => a + b.newValue, 0);
  const oldPricing = computePricing({ baseCost: costOld, quantity: 1, marginRate: 0.2 });
  const newPricing = computePricing({ baseCost: costNew, quantity: 1, marginRate: 0.25 });
  return (
    <div className="space-y-3">
      <div className="grid gap-2 md:grid-cols-4">
        <div className="rounded border p-2 text-sm">From: {fromVersion}</div>
        <div className="rounded border p-2 text-sm">To: {toVersion}</div>
        <div className="rounded border p-2 text-sm">Cost Δ: {(newPricing.totalCost - oldPricing.totalCost).toFixed(2)}</div>
        <div className="rounded border p-2 text-sm">Profit Δ: {(newPricing.profit - oldPricing.profit).toFixed(2)}</div>
      </div>
      <div className="rounded border">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th className="p-2">BOM Item</th>
              <th className="p-2">Old</th>
              <th className="p-2">New</th>
              <th className="p-2">Change</th>
            </tr>
          </thead>
          <tbody>
            {diffRows.map((row) => (
              <tr
                key={row.item}
                className={
                  row.changeType === "added"
                    ? "bg-green-50/70"
                    : row.changeType === "removed"
                      ? "bg-red-50/70"
                      : "bg-amber-50/70"
                }
              >
                <td className="p-2">{row.item}</td>
                <td className="p-2">{row.oldValue}</td>
                <td className="p-2">{row.newValue}</td>
                <td className="p-2">
                  <ChangeTag type={row.changeType} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
