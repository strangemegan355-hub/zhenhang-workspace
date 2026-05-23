import type { QueryClient, QueryKey } from "@tanstack/react-query";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type QueryDomain = "auth" | "notifications" | "quotes" | "workflow" | "files";

export type CachePolicy = "realtime" | "normal" | "static";

export type QueryPolicy = {
  domain: QueryDomain;
  cachePolicy: CachePolicy;
  staleTimeMs: number;
  gcTimeMs: number;
  retry: number | boolean;
  refetchOnWindowFocus?: boolean;
  refetchIntervalMs?: number;
};

export type RollbackStrategy = "restore-previous" | "invalidate-domain" | "noop";

const CACHE_POLICY_MS: Record<CachePolicy, { stale: number; gc: number }> = {
  realtime: { stale: 3_000, gc: 60_000 },
  normal: { stale: 30_000, gc: 5 * 60_000 },
  static: { stale: 5 * 60_000, gc: 30 * 60_000 },
};

/** Central query policy registry — domain-driven cache governance. */
export const queryPolicyRegistry: Record<QueryDomain, QueryPolicy> = {
  auth: {
    domain: "auth",
    cachePolicy: "normal",
    staleTimeMs: CACHE_POLICY_MS.normal.stale,
    gcTimeMs: CACHE_POLICY_MS.normal.gc,
    retry: 1,
    refetchOnWindowFocus: false,
  },
  notifications: {
    domain: "notifications",
    cachePolicy: "realtime",
    staleTimeMs: CACHE_POLICY_MS.realtime.stale,
    gcTimeMs: CACHE_POLICY_MS.realtime.gc,
    retry: 1,
    refetchIntervalMs: 10_000,
  },
  quotes: {
    domain: "quotes",
    cachePolicy: "normal",
    staleTimeMs: CACHE_POLICY_MS.normal.stale,
    gcTimeMs: CACHE_POLICY_MS.normal.gc,
    retry: 2,
  },
  workflow: {
    domain: "workflow",
    cachePolicy: "normal",
    staleTimeMs: CACHE_POLICY_MS.normal.stale,
    gcTimeMs: CACHE_POLICY_MS.normal.gc,
    retry: 1,
  },
  files: {
    domain: "files",
    cachePolicy: "static",
    staleTimeMs: CACHE_POLICY_MS.static.stale,
    gcTimeMs: CACHE_POLICY_MS.static.gc,
    retry: 1,
  },
};

/** Rollback strategy registry — maps mutation kinds to recovery behavior. */
export const rollbackStrategyRegistry: Record<string, RollbackStrategy> = {
  "notifications.markRead": "restore-previous",
  "quotes.update": "invalidate-domain",
  "workflow.transition": "invalidate-domain",
  default: "restore-previous",
};

export function getQueryPolicy(domain: QueryDomain): QueryPolicy {
  return queryPolicyRegistry[domain];
}

export function getRollbackStrategy(mutationKey: string): RollbackStrategy {
  return rollbackStrategyRegistry[mutationKey] ?? rollbackStrategyRegistry.default;
}

export function qk(domain: string, resource: string, params?: unknown): QueryKey {
  return params ? [domain, resource, params] : [domain, resource];
}

export async function executeRollback({
  strategy,
  rollback,
  queryClient,
  domain,
  mutationKey = "unknown",
}: {
  strategy: RollbackStrategy;
  rollback?: () => void;
  queryClient: QueryClient;
  domain: string;
  mutationKey?: string;
}) {
  runtimeTelemetry.recordRollback(mutationKey, strategy);
  runtimeTelemetry.log("warn", `query.rollback:${mutationKey}`, { strategy, domain });
  if (strategy === "restore-previous") rollback?.();
  if (strategy === "invalidate-domain") {
    await queryClient.invalidateQueries({ queryKey: [domain] });
  }
}

export async function optimisticWithPolicy<T>({
  queryClient,
  key,
  mutationKey,
  updater,
}: {
  queryClient: QueryClient;
  key: QueryKey;
  mutationKey: string;
  updater: (old: T | undefined) => T;
}) {
  await queryClient.cancelQueries({ queryKey: key });
  const previous = queryClient.getQueryData<T>(key);
  queryClient.setQueryData<T>(key, (old) => updater(old));
  const strategy = getRollbackStrategy(mutationKey);
  const domain = String(key[0] ?? "");
  const hadCache = previous !== undefined;
  runtimeTelemetry.recordCacheHit(JSON.stringify(key), hadCache);

  return () =>
    executeRollback({
      strategy,
      mutationKey,
      rollback: () => queryClient.setQueryData(key, previous),
      queryClient,
      domain,
    });
}

export function recordQueryExecution(domain: QueryDomain, resource: string) {
  runtimeTelemetry.increment("query.execute");
  const span = runtimeTelemetry.startSpan(`${domain}.${resource}`, domain);
  return () => runtimeTelemetry.endSpan(span);
}

export function invalidateByDomain(queryClient: QueryClient, domain: QueryDomain) {
  return queryClient.invalidateQueries({ queryKey: [domain] });
}
