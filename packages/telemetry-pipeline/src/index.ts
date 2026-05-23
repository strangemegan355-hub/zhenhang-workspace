import { runtimeBus } from "@zhenhang/runtime-bus";
import { runtimeTelemetry, type PerformanceSnapshot, type TraceSpan } from "@zhenhang/runtime-telemetry";

export type TelemetryBatch = {
  spans: TraceSpan[];
  metrics: Record<string, number>;
  snapshot: PerformanceSnapshot;
  exportedAt: string;
};

export type MetricsTransport = (batch: TelemetryBatch) => void | Promise<void>;

/** Telemetry pipeline — batching, aggregation, analytics, transport. */
export class TelemetryPipeline {
  private batch: TraceSpan[] = [];
  private batchSize = 50;
  private flushIntervalMs = 5000;
  private timer: ReturnType<typeof setInterval> | null = null;
  private transport: MetricsTransport;

  constructor(transport?: MetricsTransport) {
    this.transport =
      transport ??
      ((batch) => {
        if (process.env.NODE_ENV !== "production") {
          console.info("[telemetry-pipeline]", batch.exportedAt, batch.metrics);
        }
      });
  }

  start() {
    if (this.timer) return;
    this.timer = setInterval(() => this.flush(), this.flushIntervalMs);
    runtimeBus.dispatch({ type: "telemetry.pipeline.start", domain: "telemetry" });
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.flush();
    runtimeBus.dispatch({ type: "telemetry.pipeline.stop", domain: "telemetry" });
  }

  ingestSpan(span: TraceSpan) {
    this.batch.push(span);
    if (this.batch.length >= this.batchSize) this.flush();
  }

  aggregate(): Record<string, number> {
    const metrics = runtimeTelemetry.getMetrics();
    const spans = runtimeTelemetry.getSpans().filter((s) => s.durationMs != null);
    const avgMs =
      spans.length > 0 ? spans.reduce((a, s) => a + (s.durationMs ?? 0), 0) / spans.length : 0;
    return {
      ...metrics,
      "analytics.span.count": spans.length,
      "analytics.span.avg_ms": avgMs,
      "analytics.rollback.count": runtimeTelemetry.getRollbacks().length,
    };
  }

  async flush() {
    if (this.batch.length === 0 && Object.keys(runtimeTelemetry.getMetrics()).length === 0) return;
    const batch: TelemetryBatch = {
      spans: [...this.batch, ...runtimeTelemetry.getSpans().slice(0, this.batchSize)],
      metrics: this.aggregate(),
      snapshot: runtimeTelemetry.snapshot(),
      exportedAt: new Date().toISOString(),
    };
    this.batch = [];
    await this.transport(batch);
    runtimeBus.dispatch({ type: "telemetry.pipeline.flush", domain: "telemetry", payload: { size: batch.spans.length } });
  }

  exportSnapshot(): PerformanceSnapshot {
    return runtimeTelemetry.snapshot();
  }
}

export const telemetryPipeline = new TelemetryPipeline();

/** Bridge runtime-telemetry spans into pipeline. */
runtimeBus.on("telemetry.span", (evt) => {
  const span = evt.payload as TraceSpan | undefined;
  if (span?.id) telemetryPipeline.ingestSpan(span);
});
