import { eventStreamRuntime } from "@zhenhang/event-stream";
import { parseEnvelope, type RealtimeEnvelope } from "@zhenhang/realtime-protocol";
import { runtimeBus } from "@zhenhang/runtime-bus";

export type WorkerNode = {
  id: string;
  role: "coordinator" | "worker";
  lastSeenAt: string;
};

export type PubSubBridge = {
  publish: (channel: string, message: string) => void | Promise<void>;
  subscribe: (channel: string, handler: (message: string) => void) => () => void;
};

/** In-memory pub/sub bridge (browser dev); swap for Redis in worker/node. */
export function createMemoryPubSubBridge(): PubSubBridge {
  const subs = new Map<string, Set<(msg: string) => void>>();
  return {
    publish: (channel, message) => {
      subs.get(channel)?.forEach((fn) => fn(message));
    },
    subscribe: (channel, handler) => {
      if (!subs.has(channel)) subs.set(channel, new Set());
      subs.get(channel)!.add(handler);
      return () => subs.get(channel)?.delete(handler);
    },
  };
}

/** Distributed runtime — sync, worker mesh, cross-worker propagation. */
export class DistributedRuntime {
  private workerId: string;
  private mesh = new Map<string, WorkerNode>();
  private bridge: PubSubBridge;
  private unsubscribers: Array<() => void> = [];

  constructor(options?: { workerId?: string; bridge?: PubSubBridge }) {
    this.workerId = options?.workerId ?? `worker-${typeof crypto !== "undefined" ? crypto.randomUUID().slice(0, 8) : Date.now()}`;
    this.bridge = options?.bridge ?? createMemoryPubSubBridge();
    this.registerWorker({ id: this.workerId, role: "coordinator", lastSeenAt: new Date().toISOString() });
  }

  getWorkerId() {
    return this.workerId;
  }

  registerWorker(node: WorkerNode) {
    this.mesh.set(node.id, node);
  }

  getMesh(): WorkerNode[] {
    return [...this.mesh.values()];
  }

  /** Redis-style channel: runtime:events */
  connect(channel = "runtime:events") {
    const unsub = this.bridge.subscribe(channel, (raw) => {
      const envelope = parseEnvelope(JSON.parse(raw));
      if (!envelope) return;
      eventStreamRuntime.ingest(envelope);
      void runtimeBus.dispatch({
        type: "distributed.event",
        domain: envelope.channel,
        payload: { workerId: this.workerId, envelope },
      });
    });
    this.unsubscribers.push(unsub);
    runtimeBus.dispatch({ type: "distributed.connect", domain: "runtime", payload: { channel, workerId: this.workerId } });
  }

  propagate(envelope: RealtimeEnvelope) {
    const channel = "runtime:events";
    this.bridge.publish(channel, JSON.stringify(envelope));
    eventStreamRuntime.ingest(envelope);
  }

  sync() {
    const peers = this.getMesh().filter((w) => w.id !== this.workerId);
    runtimeBus.dispatch({ type: "distributed.sync", domain: "runtime", payload: { workerId: this.workerId, peers } });
    return { workerId: this.workerId, peers };
  }

  disconnect() {
    this.unsubscribers.forEach((fn) => fn());
    this.unsubscribers = [];
  }
}

export const distributedRuntime = new DistributedRuntime();
