import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type StoredEvent = {
  offset: number;
  partition: string;
  eventId: string;
  payload: unknown;
  at: string;
};

export type SnapshotMerge = {
  baseOffset: number;
  snapshotId: string;
  mergedAt: string;
};

/** Append-only runtime event store with partitions, compaction, replay cursor. */
export class RuntimeEventStore {
  private log: StoredEvent[] = [];
  private partitions = new Map<string, StoredEvent[]>();
  private cursors = new Map<string, number>();
  private snapshots = new Map<string, SnapshotMerge>();
  private offset = 0;

  append(partition: string, eventId: string, payload: unknown): StoredEvent {
    this.offset += 1;
    const evt: StoredEvent = {
      offset: this.offset,
      partition,
      eventId,
      payload,
      at: new Date().toISOString(),
    };
    this.log.push(evt);
    if (!this.partitions.has(partition)) this.partitions.set(partition, []);
    this.partitions.get(partition)!.push(evt);
    return evt;
  }

  readPartition(partition: string, fromOffset = 0): StoredEvent[] {
    return (this.partitions.get(partition) ?? []).filter((e) => e.offset >= fromOffset);
  }

  setReplayCursor(consumerId: string, offset: number) {
    this.cursors.set(consumerId, offset);
  }

  getReplayCursor(consumerId: string): number {
    return this.cursors.get(consumerId) ?? 0;
  }

  replay(consumerId: string, partition?: string): StoredEvent[] {
    const from = this.getReplayCursor(consumerId);
    const source = partition ? this.readPartition(partition, from) : this.log.filter((e) => e.offset >= from);
    if (source.length) {
      const last = source[source.length - 1].offset;
      this.setReplayCursor(consumerId, last + 1);
    }
    return source;
  }

  /** Merge snapshot — compact events before base offset. */
  mergeSnapshot(snapshotId: string, upToOffset: number) {
    this.snapshots.set(snapshotId, {
      baseOffset: upToOffset,
      snapshotId,
      mergedAt: new Date().toISOString(),
    });
    runtimeTelemetry.log("info", "event-store.snapshot.merge", { snapshotId, upToOffset });
  }

  compact(retainFromOffset: number) {
    const before = this.log.length;
    this.log = this.log.filter((e) => e.offset >= retainFromOffset);
    for (const [p, events] of this.partitions) {
      this.partitions.set(
        p,
        events.filter((e) => e.offset >= retainFromOffset),
      );
    }
    runtimeTelemetry.increment("event-store.compact", before - this.log.length);
  }

  stats() {
    return {
      total: this.log.length,
      partitions: this.partitions.size,
      snapshots: this.snapshots.size,
      maxOffset: this.offset,
    };
  }
}

export const runtimeEventStore = new RuntimeEventStore();
