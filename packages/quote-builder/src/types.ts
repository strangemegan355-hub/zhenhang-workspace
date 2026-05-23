export type QuoteLineRow = {
  item_code: string;
  item_name: string;
  unit: string;
  quantity: number;
  unit_price: number;
  unit_cost?: number;
};

export type BomTreeNode = {
  id: string;
  code: string;
  name: string;
  quantity: number;
  unitCost: number;
  lineTotal: number;
  children?: BomTreeNode[];
};

export type ExportTemplateOption = {
  id: string;
  name: string;
  format: "pdf" | "xlsx";
  description?: string;
};

export type WorkflowActionOption = {
  action_code: string;
  action_name: string;
};

export type ApprovalRecordView = {
  actor: string;
  action: string;
  at: string;
  comment?: string;
};

export type CostBreakdownSlice = {
  label: string;
  value: number;
  color: string;
};
