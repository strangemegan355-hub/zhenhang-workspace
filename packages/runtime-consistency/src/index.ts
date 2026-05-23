import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type OrderedEvent = {
  sequence: number;
  eventId: string;
  type: string;
  payload: unknown;
  at: string;
};

export type SnapshotVersion = {
  version: number;
  checkpointId: string;
  at: string;
  hash: string;
};

/** Runtime consistency — ordering, idempotency, replay, snapshot versioning. */
export class RuntimeConsistencyLayer {
  private sequence = 0;
  private log: OrderedEvent[] = [];
  private processedIds = new Set<string>();
  private versions: SnapshotVersion[] = [];

  /** Append with monotonic sequence (event ordering). */
  append(eventId: string, type: string, payload: unknown): OrderedEvent {
    this.sequence += 1;
    const evt: OrderedEvent = {
      sequence: this.sequence,
      eventId,
      type,
      payload,
      at: new Date().toISOString(),
    };
    this.log.push(evt);
    if (this.log.length > 1000) this.log.shift();
    return evt;
  }

  /** Idempotent handler — skip duplicate event_id. */
  processOnce(eventId: string, handler: () => void | Promise<void>): boolean {
    if (this.processedIds.has(eventId)) {
      runtimeTelemetry.increment("consistency.idempotent.skip");
      return false;
    }
    this.processedIds.add(eventId);
    if (this.processedIds.size > 5000) {
      const arr = [...this.processedIds].slice(-2500);
      this.processedIds = new Set(arr);
    }
    void Promise.resolve(handler());
    return true;
  }

  /** Replay log from sequence cursor (replay consistency). */
  replay(fromSequence = 0): OrderedEvent[] {
    return this.log.filter((e) => e.sequence >= fromSequence);
  }

  registerSnapshotVersion(checkpointId: string, hash: string): SnapshotVersion {
    const version: SnapshotVersion = {
      version: this.versions.length + 1,
      checkpointId,
      at: new Date().toISOString(),
      hash,
    };
    this.versions.unshift(version);
    if (this.versions.length > 50) this.versions.pop();
    return version;
  }

  /** Validate recovery against latest snapshot version. */
  validateRecovery(checkpointId: string, hash: string): boolean {
    const latest = this.versions[0];
    if (!latest) return true;
    const ok = latest.checkpointId === checkpointId && latest.hash === hash;
    runtimeTelemetry.log(ok ? "info" : "warn", "consistency.recovery.validation", { ok, checkpointId });
    return ok;
  }

  getLatestVersion(): SnapshotVersion | undefined {
    return this.versions[0];
  }

  stats() {
    return {
      sequence: this.sequence,
      logSize: this.log.length,
      processedIds: this.processedIds.size,
      versions: this.versions.length,
    };
  }
}

export const runtimeConsistency = new RuntimeConsistencyLayer();

export function hashSnapshot(data: unknown): string {
  const str = JSON.stringify(data);
  let h = 0;
  for (let i = 0; i < str.length; i += 1) h = (h << 5) - h + str.charCodeAt(i);
  return `h${Math.abs(h).toString(16)}`;
}
