import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type RetryPolicy = {
  maxAttempts: number;
  baseDelayMs: number;
  multiplier: number;
};

export type CircuitState = "closed" | "open" | "half_open";

export type RuntimeMode = "normal" | "degraded" | "isolated";

/** Fault tolerance — retry, circuit breaker, fallback, isolation, degraded mode. */
export class RuntimeFaultTolerance {
  private retryPolicy: RetryPolicy = { maxAttempts: 3, baseDelayMs: 200, multiplier: 2 };
  private circuits = new Map<string, { state: CircuitState; failures: number; openedAt?: number }>();
  private isolatedNodes = new Set<string>();
  private mode: RuntimeMode = "normal";
  private failureThreshold = 5;
  private openMs = 10_000;

  setRetryPolicy(policy: Partial<RetryPolicy>) {
    this.retryPolicy = { ...this.retryPolicy, ...policy };
  }

  setMode(mode: RuntimeMode) {
    this.mode = mode;
    runtimeTelemetry.log("info", `runtime.mode.${mode}`);
  }

  getMode(): RuntimeMode {
    return this.mode;
  }

  isolateNode(nodeId: string) {
    this.isolatedNodes.add(nodeId);
  }

  isIsolated(nodeId: string): boolean {
    return this.isolatedNodes.has(nodeId);
  }

  getCircuit(key: string) {
    return this.circuits.get(key) ?? { state: "closed" as CircuitState, failures: 0 };
  }

  private recordSuccess(key: string) {
    this.circuits.set(key, { state: "closed", failures: 0 });
  }

  private recordFailure(key: string) {
    const c = this.circuits.get(key) ?? { state: "closed" as CircuitState, failures: 0 };
    c.failures += 1;
    if (c.failures >= this.failureThreshold) {
      c.state = "open";
      c.openedAt = Date.now();
      runtimeTelemetry.log("warn", "circuit.open", { key });
    }
    this.circuits.set(key, c);
  }

  canExecute(key: string): boolean {
    if (this.mode === "isolated") return false;
    const c = this.getCircuit(key);
    if (c.state === "open") {
      if (c.openedAt && Date.now() - c.openedAt > this.openMs) {
        this.circuits.set(key, { state: "half_open", failures: 0 });
        return true;
      }
      return this.mode === "degraded";
    }
    return true;
  }

  async withRetry<T>(key: string, fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (!this.canExecute(key)) {
      if (fallback) return fallback();
      throw new Error(`Circuit open or runtime isolated: ${key}`);
    }
    let delay = this.retryPolicy.baseDelayMs;
    for (let attempt = 1; attempt <= this.retryPolicy.maxAttempts; attempt += 1) {
      try {
        const result = await fn();
        this.recordSuccess(key);
        return result;
      } catch (err) {
        this.recordFailure(key);
        runtimeTelemetry.increment("fault.retry");
        if (attempt >= this.retryPolicy.maxAttempts) {
          if (this.mode !== "normal") this.setMode("degraded");
          if (fallback) return fallback();
          throw err;
        }
        await new Promise((r) => setTimeout(r, delay));
        delay *= this.retryPolicy.multiplier;
      }
    }
    throw new Error("Retry exhausted");
  }

  stats() {
    return {
      mode: this.mode,
      circuits: Object.fromEntries(this.circuits),
      isolated: [...this.isolatedNodes],
      retryPolicy: this.retryPolicy,
    };
  }
}

export const runtimeFaultTolerance = new RuntimeFaultTolerance();
