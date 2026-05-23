import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type SchedulePriority = "critical" | "high" | "normal" | "low";

const PRIORITY_WEIGHT: Record<SchedulePriority, number> = {
  critical: 0,
  high: 1,
  normal: 2,
  low: 3,
};

export type ScheduledTask<T = unknown> = {
  id: string;
  domain: string;
  priority: SchedulePriority;
  fn: () => Promise<T>;
  createdAt: number;
};

export type SchedulingPolicy = {
  maxConcurrency: number;
  maxQueuePerDomain: number;
  backpressureThreshold: number;
};

const DEFAULT_POLICY: SchedulingPolicy = {
  maxConcurrency: 8,
  maxQueuePerDomain: 100,
  backpressureThreshold: 80,
};

/** Runtime scheduler — priority queue, concurrency, domain isolation, backpressure. */
export class RuntimeScheduler {
  private policy: SchedulingPolicy;
  private queue: ScheduledTask[] = [];
  private running = 0;
  private domainRunning = new Map<string, number>();
  private paused = false;

  constructor(policy: Partial<SchedulingPolicy> = {}) {
    this.policy = { ...DEFAULT_POLICY, ...policy };
  }

  enqueue<T>(task: Omit<ScheduledTask<T>, "createdAt">): boolean {
    const domainCount = this.queue.filter((t) => t.domain === task.domain).length;
    if (domainCount >= this.policy.maxQueuePerDomain) {
      runtimeTelemetry.log("warn", "scheduler.backpressure.domain", { domain: task.domain });
      return false;
    }
    if (this.queue.length >= this.policy.backpressureThreshold) {
      runtimeTelemetry.log("warn", "scheduler.backpressure.global", { size: this.queue.length });
      return false;
    }
    this.queue.push({ ...task, createdAt: Date.now() } as ScheduledTask);
    this.queue.sort((a, b) => PRIORITY_WEIGHT[a.priority] - PRIORITY_WEIGHT[b.priority]);
    void this.pump();
    return true;
  }

  private async pump() {
    if (this.paused || this.running >= this.policy.maxConcurrency) return;
    const next = this.queue.shift();
    if (!next) return;
    this.running += 1;
    this.domainRunning.set(next.domain, (this.domainRunning.get(next.domain) ?? 0) + 1);
    const span = runtimeTelemetry.startSpan(`scheduler.${next.domain}`, "runtime");
    try {
      await next.fn();
      runtimeTelemetry.increment("scheduler.task.success");
    } catch (err) {
      runtimeTelemetry.increment("scheduler.task.error");
      runtimeTelemetry.log("error", `scheduler.task:${next.id}`, err);
    } finally {
      this.running -= 1;
      this.domainRunning.set(next.domain, Math.max(0, (this.domainRunning.get(next.domain) ?? 1) - 1));
      runtimeTelemetry.endSpan(span);
      void this.pump();
    }
  }

  pause() {
    this.paused = true;
  }

  resume() {
    this.paused = false;
    void this.pump();
  }

  stats() {
    return {
      queued: this.queue.length,
      running: this.running,
      domainRunning: Object.fromEntries(this.domainRunning),
      policy: this.policy,
    };
  }
}

export const runtimeScheduler = new RuntimeScheduler();
