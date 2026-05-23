import { qk } from "@zhenhang/query-policy-registry";

export const queryKeys = {
  auth: {
    currentUser: () => qk("auth", "current-user"),
  },
  quotes: {
    list: (params: { page: number; keyword?: string }) => qk("quotes", "list", params),
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
  master: {
    customers: (page: number, q?: string) => qk("master", "customers", { page, q }),
    machines: (page: number, q?: string) => qk("master", "machines", { page, q }),
    boms: (page: number, q?: string) => qk("master", "boms", { page, q }),
    approvalTemplates: (page: number) => qk("master", "approval-templates", page),
  },
};
