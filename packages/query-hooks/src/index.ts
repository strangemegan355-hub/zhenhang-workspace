export * from "./keys";
export * from "./domains/auth";
export * from "./domains/notifications";
export * from "./domains/quotes";
export * from "./domains/boms";
export * from "./domains/workflow";
export * from "./domains/ai";
export * from "./domains/dashboard";
export * from "./domains/master";
export * from "./domains/workshop";

export {
  getQueryPolicy,
  getRollbackStrategy,
  invalidateByDomain,
  optimisticWithPolicy,
  qk,
  queryPolicyRegistry,
  rollbackStrategyRegistry,
} from "@zhenhang/query-policy-registry";
