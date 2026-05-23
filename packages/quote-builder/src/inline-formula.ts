import type { QuoteLineRow } from "./types";

export type LineFormulaView = {
  lineTotal: number;
  cost: number;
  margin: number;
  marginPct: number;
};

export function computeLineFormula(row: QuoteLineRow, marginRate: number): LineFormulaView {
  const lineTotal = row.quantity * row.unit_price;
  const cost = row.quantity * (row.unit_cost ?? row.unit_price * 0.7);
  const margin = lineTotal - cost;
  const marginPct = lineTotal > 0 ? (margin / lineTotal) * 100 : 0;
  return { lineTotal, cost, margin, marginPct };
}

export function formatFormulaExpr(row: QuoteLineRow): string {
  return `${row.quantity} × ${row.unit_price.toFixed(2)}`;
}
