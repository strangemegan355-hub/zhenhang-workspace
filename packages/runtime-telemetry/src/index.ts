export type TraceSpan = {
  id: string;
  name: string;
  domain: string;
  startedAt: number;
  durationMs?: number;
  meta?: Record<string, unknown>;
};

export type CacheHitRecord = {
  key: string;
  hit: boolean;
  at: string;
};

export type RollbackRecord = {
  mutationKey: string;
  strategy: string;
  at: string;
};

export type PerformanceSnapshot = {
  at: string;
  queryCount: number;
  cacheHitRate: number;
  avgSpanMs: number;
  rollbackCount: number;
};

type LogLevel = "debug" | "info" | "warn" | "error";

class RuntimeTelemetryHub {
  private metrics = new Map<string, number>();
  private spans: TraceSpan[] = [];
  private cacheHits: CacheHitRecord[] = [];
  private rollbacks: RollbackRecord[] = [];
  private logs: Array<{ level: LogLevel; message: string; at: string; meta?: unknown }> = [];
  private maxBuffer = 200;

  increment(metric: string, delta = 1) {
    this.metrics.set(metric, (this.metrics.get(metric) ?? 0) + delta);
  }

  startSpan(name: string, domain: string, meta?: Record<string, unknown>): string {
    const id = `${domain}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    this.spans.unshift({ id, name, domain, startedAt: performance.now(), meta });
    if (this.spans.length > this.maxBuffer) this.spans.pop();
    return id;
  }

  endSpan(id: string) {
    const span = this.spans.find((s) => s.id === id);
    if (!span) return;
    span.durationMs = performance.now() - span.startedAt;
  }

  recordCacheHit(key: string, hit: boolean) {
    this.cacheHits.unshift({ key, hit, at: new Date().toISOString() });
    if (this.cacheHits.length > this.maxBuffer) this.cacheHits.pop();
    this.increment(hit ? "cache.hit" : "cache.miss");
  }

  recordRollback(mutationKey: string, strategy: string) {
    this.rollbacks.unshift({ mutationKey, strategy, at: new Date().toISOString() });
    if (this.rollbacks.length > this.maxBuffer) this.rollbacks.pop();
    this.increment("rollback.total");
  }

  log(level: LogLevel, message: string, meta?: unknown) {
    this.logs.unshift({ level, message, at: new Date().toISOString(), meta });
    if (this.logs.length > this.maxBuffer) this.logs.pop();
    if (typeof console !== "undefined" && process.env.NODE_ENV !== "production") {
      console[level](`[runtime] ${message}`, meta ?? "");
    }
  }

  getMetrics(): Record<string, number> {
    return Object.fromEntries(this.metrics);
  }

  getSpans(): TraceSpan[] {
    return [...this.spans];
  }

  getCacheHits(): CacheHitRecord[] {
    return [...this.cacheHits];
  }

  getRollbacks(): RollbackRecord[] {
    return [...this.rollbacks];
  }

  getLogs(): typeof this.logs {
    return [...this.logs];
  }

  snapshot(): PerformanceSnapshot {
    const hits = this.cacheHits.filter((c) => c.hit).length;
    const total = this.cacheHits.length || 1;
    const completed = this.spans.filter((s) => s.durationMs != null);
    const avgSpanMs =
      completed.length > 0
        ? completed.reduce((sum, s) => sum + (s.durationMs ?? 0), 0) / completed.length
        : 0;
    return {
      at: new Date().toISOString(),
      queryCount: this.metrics.get("query.execute") ?? 0,
      cacheHitRate: hits / total,
      avgSpanMs,
      rollbackCount: this.rollbacks.length,
    };
  }
}

export const runtimeTelemetry = new RuntimeTelemetryHub();

export async function traceAsync<T>(name: string, domain: string, fn: () => Promise<T>): Promise<T> {
  const id = runtimeTelemetry.startSpan(name, domain);
  try {
    return await fn();
  } finally {
    runtimeTelemetry.endSpan(id);
  }
}
