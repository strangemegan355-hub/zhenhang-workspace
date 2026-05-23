import { evaluatePricingFormulas, type FormulaContext } from "@zhenhang/formula-engine";

export type QuoteBlockId = "equipment_bom" | "configurator" | "cost_profit" | "approval_flow";

export type LayoutBlock = {
  id: QuoteBlockId;
  title: string;
  row: "main" | "bottom";
  span?: number;
};

export type BlockComponentProps = { title: string; runtime: QuoteRuntime };

export type BlockComponent = (props: BlockComponentProps) => unknown;

export type BlockRegistry = Record<string, BlockComponent>;

export type PricingInput = {
  baseCost: number;
  quantity: number;
  marginRate: number;
  discountRate?: number;
};

export type ComputedQuoteFields = {
  subtotal: number;
  discount: number;
  totalCost: number;
  revenue: number;
  profit: number;
  marginPercent: number;
};

/** Pricing formula engine — deterministic quote calculations. */
export function computePricing(input: PricingInput): ComputedQuoteFields {
  const discountRate = input.discountRate ?? 0;
  const subtotal = input.baseCost * input.quantity;
  const discount = subtotal * discountRate;
  const totalCost = subtotal - discount;
  const revenue = totalCost * (1 + input.marginRate);
  const profit = revenue - totalCost;
  const marginPercent = revenue > 0 ? (profit / revenue) * 100 : 0;
  return { subtotal, discount, totalCost, revenue, profit, marginPercent };
}

/** Computed field engine — derived fields from runtime state. */
export function computeFields(state: {
  lines: Array<{ sku: string; qty: number; unitCost: number }>;
  marginRate: number;
  discountRate?: number;
}): ComputedQuoteFields & { lineCount: number } {
  const baseCost = state.lines.reduce((sum, l) => sum + l.qty * l.unitCost, 0);
  const quantity = state.lines.reduce((sum, l) => sum + l.qty, 0);
  const pricing = computePricing({
    baseCost: quantity > 0 ? baseCost / quantity : baseCost,
    quantity: Math.max(quantity, 1),
    marginRate: state.marginRate,
    discountRate: state.discountRate,
  });
  return { ...pricing, lineCount: state.lines.length };
}

/** Block runtime — registry + dynamic layout resolution. */
export class QuoteRuntime {
  private registry: BlockRegistry;
  private layout: LayoutBlock[];

  constructor(options?: { registry?: BlockRegistry; layout?: LayoutBlock[] }) {
    this.registry = options?.registry ?? {};
    this.layout = options?.layout ?? defaultQuoteLayout;
  }

  getLayout(): LayoutBlock[] {
    return this.layout;
  }

  setLayout(layout: LayoutBlock[]) {
    this.layout = layout;
  }

  resolveBlock(id: string): BlockRegistry[string] | undefined {
    return this.registry[id];
  }

  getMainBlocks(): LayoutBlock[] {
    return this.layout.filter((b) => b.row === "main");
  }

  getBottomBlocks(): LayoutBlock[] {
    return this.layout.filter((b) => b.row === "bottom");
  }
}

export const defaultQuoteLayout: LayoutBlock[] = [
  { id: "equipment_bom", title: "Equipment / BOM", row: "main", span: 3 },
  { id: "configurator", title: "Configurator", row: "main", span: 6 },
  { id: "cost_profit", title: "Cost / Profit", row: "main", span: 3 },
  { id: "approval_flow", title: "Approval Workflow", row: "bottom" },
];

export function createQuoteRuntime(options?: { registry?: BlockRegistry; layout?: LayoutBlock[] }) {
  return new QuoteRuntime(options);
}

/** Dynamic pricing via formula-engine (sandbox + dependency graph + cache). */
export function computePricingViaFormulas(
  formulas: Record<string, string>,
  ctx: FormulaContext,
): Record<string, number> {
  return evaluatePricingFormulas(formulas, ctx);
}

export { evaluatePricingFormulas } from "@zhenhang/formula-engine";
