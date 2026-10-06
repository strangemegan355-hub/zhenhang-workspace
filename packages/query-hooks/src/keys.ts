import { qk } from "@zhenhang/query-policy-registry";

export const queryKeys = {
  auth: {
    currentUser: () => qk("auth", "current-user"),
  },
  quotes: {
    list: (params: { page: number; keyword?: string; quoteKind?: string }) =>
      qk("quotes", "list", params),
    detail: (quoteId: string) => qk("quotes", "detail", quoteId),
    diff: (quoteId: string, fromVersionNo: number, toVersionNo: number) =>
      qk("quotes", "diff", { quoteId, fromVersionNo, toVersionNo }),
    approvals: (quoteId: string) => qk("quotes", "approvals", quoteId),
    exportTask: (taskId: string) => qk("quotes", "export-task", taskId),
    copilot: (quoteId: string, from?: number, to?: number) =>
      qk("quotes", "copilot", { quoteId, from, to }),
    exportTemplates: () => qk("quotes", "export-templates"),
  },
  boms: {
    detail: (bomId: string) => qk("boms", "detail", bomId),
    items: (bomId: string, page: number) => qk("boms", "items", { bomId, page }),
  },
  workflow: {
    actions: (entityType: string, currentState: string) =>
      qk("workflow", "actions", { entityType, currentState }),
  },
  notifications: {
    list: (params: { page: number; keyword?: string; unreadOnly?: boolean; status?: string }) =>
      qk("notifications", "list", params),
    unreadCount: () => qk("notifications", "unread-count"),
  },
  dashboard: {
    overview: () => qk("dashboard", "overview"),
  },
  workshop: {
    board: () => qk("workshop", "board"),
  },
  costing: {
    list: (page: number, q?: string) => qk("costing", "list", { page, q }),
    detail: (id: string) => qk("costing", "detail", id),
  },
  projects: {
    list: (page: number, q?: string) => qk("projects", "list", { page, q }),
    summary: (id: string) => qk("projects", "summary", id),
    profitLedger: (page: number, q?: string, overBudgetOnly?: boolean) =>
      qk("projects", "profit-ledger", { page, q, overBudgetOnly }),
  },
  actualCosts: {
    list: (projectId: string, page?: number) => qk("actualCosts", "list", { projectId, page }),
  },
  procurement: {
    list: (page: number, q?: string, status?: string) => qk("procurement", "list", { page, q, status }),
  },
  workOrders: {
    list: (page: number, q?: string, status?: string, projectId?: string) =>
      qk("workOrders", "list", { page, q, status, projectId }),
    summary: () => qk("workOrders", "summary"),
  },
  fieldwork: {
    list: (page: number, q?: string, recordType?: string, status?: string) =>
      qk("fieldwork", "list", { page, q, recordType, status }),
    summary: () => qk("fieldwork", "summary"),
  },
  accounting: {
    status: () => qk("accounting", "status"),
    list: (page: number, customerId?: string, supplierId?: string, entryKind?: string, includeVoid?: boolean) =>
      qk("accounting", "list", { page, customerId, supplierId, entryKind, includeVoid }),
    quoteReceivableRequests: (page: number, approvalStatus?: string) =>
      qk("accounting", "quote-receivable-requests", { page, approvalStatus }),
    quoteReceivableByQuote: (quoteId: string) => qk("accounting", "quote-receivable-by-quote", quoteId),
    ledgerCustomers: (page: number, outstandingOnly?: boolean, q?: string) =>
      qk("accounting", "ledger-customers", { page, outstandingOnly, q }),
    ledgerDetail: (customerId: string) => qk("accounting", "ledger-detail", customerId),
  },
  master: {
    customers: (page: number, q?: string) => qk("master", "customers", { page, q }),
    machines: (page: number, q?: string, pageSize?: number) =>
      qk("master", "machines", { page, q, pageSize }),
    boms: (page: number, q?: string) => qk("master", "boms", { page, q }),
    materials: (page: number, q?: string, categoryId?: string) => qk("master", "materials", { page, q, categoryId }),
    suppliers: (page: number, q?: string) => qk("master", "suppliers", { page, q }),
    units: (page: number, q?: string) => qk("master", "units", { page, q }),
    materialCategories: (page: number, q?: string) => qk("master", "material-categories", { page, q }),
    productCategories: (page: number, q?: string) => qk("master", "product-categories", { page, q }),
    products: (page: number, q?: string, categoryId?: string) => qk("master", "products", { page, q, categoryId }),
    productCostTemplates: (page: number, q?: string, productId?: string) =>
      qk("master", "product-cost-templates", { page, q, productId }),
    productPriceTemplates: (page: number, q?: string, productId?: string) =>
      qk("master", "product-price-templates", { page, q, productId }),
    productQuotePayload: (productId: string, costTemplateId?: string, priceTemplateId?: string) =>
      qk("master", "product-quote-payload", { productId, costTemplateId, priceTemplateId }),
    machineCategories: (page: number, q?: string) => qk("master", "machine-categories", { page, q }),
    machineParameters: (page: number, machineId?: string, q?: string) =>
      qk("master", "machine-parameters", { page, machineId, q }),
    machineImages: (page: number, machineId?: string, q?: string) =>
      qk("master", "machine-images", { page, machineId, q }),
    approvalTemplates: (page: number) => qk("master", "approval-templates", page),
  },
};
