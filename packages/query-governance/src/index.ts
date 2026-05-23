/** @deprecated Prefer @zhenhang/query-policy-registry — re-exported for backward compatibility. */
export {
  getQueryPolicy,
  getRollbackStrategy,
  invalidateByDomain,
  optimisticWithPolicy as optimisticWithRollback,
  qk,
  queryPolicyRegistry,
  rollbackStrategyRegistry,
} from "@zhenhang/query-policy-registry";

export const queryStaleTimePolicy = {
  realtime: 3_000,
  normal: 30_000,
  static: 5 * 60_000,
} as const;
