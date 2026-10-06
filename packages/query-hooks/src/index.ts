export * from "./keys";
export * from "./domains/auth";
export * from "./domains/notifications";
export * from "./domains/quotes";
export * from "./domains/boms";
export * from "./domains/workflow";
export * from "./domains/ai";
export * from "./domains/dashboard";
export * from "./domains/master";
export * from "./domains/machines";
export * from "./domains/materials";
export * from "./domains/suppliers";
export * from "./domains/business-settings";
export * from "./domains/standards";
export * from "./domains/products";
export * from "./domains/costing";
export * from "./domains/projects";
export * from "./domains/actual-costs";
export * from "./domains/procurement";
export * from "./domains/work-orders";
export * from "./domains/fieldwork";
export * from "./domains/accounting";
export * from "./domains/approval-hub";
export * from "./domains/workshop";
export * from "./domains/equipment-units";
export * from "./domains/option-groups";
export * from "./domains/aftersales";
export * from "./domains/admin";
export * from "./domains/audits";
export * from "./domains/files";

export {
  getQueryPolicy,
  getRollbackStrategy,
  invalidateByDomain,
  optimisticWithPolicy,
  qk,
  queryPolicyRegistry,
  rollbackStrategyRegistry,
} from "@zhenhang/query-policy-registry";
