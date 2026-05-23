import { runtimeBus } from "@zhenhang/runtime-bus";

export type RuntimeGraphSnapshot = {
  name: string;
  nodes: Array<{ id: string; label: string; kind: string; meta?: Record<string, unknown> }>;
  edges: Array<{ from: string; to: string; label?: string }>;
  at: string;
};

export type RuntimeCheckpoint = {
  id: string;
  at: string;
  busPhase?: string;
  graphs: Record<string, RuntimeGraphSnapshot>;
  meta?: Record<string, unknown>;
};

export type PersistenceStore = {
  get: (key: string) => string | null;
  set: (key: string, value: string) => void;
  remove: (key: string) => void;
};

function createMemoryStore(): PersistenceStore {
  const data = new Map<string, string>();
  return {
    get: (k) => data.get(k) ?? null,
    set: (k, v) => data.set(k, v),
    remove: (k) => data.delete(k),
  };
}

function createLocalStore(prefix: string): PersistenceStore {
  return {
    get: (key) => {
      if (typeof localStorage === "undefined") return null;
      return localStorage.getItem(`${prefix}:${key}`);
    },
    set: (key, value) => {
      if (typeof localStorage !== "undefined") localStorage.setItem(`${prefix}:${key}`, value);
    },
    remove: (key) => {
      if (typeof localStorage !== "undefined") localStorage.removeItem(`${prefix}:${key}`);
    },
  };
}

/** Runtime persistence — snapshot, checkpoint, replay, recovery. */
export class RuntimePersistence {
  private store: PersistenceStore;
  private checkpoints: RuntimeCheckpoint[] = [];
  private replayLog: RuntimeCheckpoint[] = [];

  constructor(store?: PersistenceStore) {
    this.store =
      store ??
      (typeof localStorage !== "undefined" ? createLocalStore("zhenhang-runtime") : createMemoryStore());
    this.loadCheckpoints();
  }

  private loadCheckpoints() {
    const raw = this.store.get("checkpoints");
    if (!raw) return;
    try {
      this.checkpoints = JSON.parse(raw) as RuntimeCheckpoint[];
    } catch {
      this.checkpoints = [];
    }
  }

  private persistCheckpoints() {
    this.store.set("checkpoints", JSON.stringify(this.checkpoints.slice(0, 20)));
  }

  snapshot(graphs: Record<string, RuntimeGraphSnapshot>, meta?: Record<string, unknown>): RuntimeCheckpoint {
    const cp: RuntimeCheckpoint = {
      id: `cp-${Date.now()}`,
      at: new Date().toISOString(),
      graphs,
      meta,
    };
    this.replayLog.unshift(cp);
    if (this.replayLog.length > 50) this.replayLog.pop();
    return cp;
  }

  checkpoint(graphs: Record<string, RuntimeGraphSnapshot>, busPhase?: string): RuntimeCheckpoint {
    const cp: RuntimeCheckpoint = {
      id: `cp-${Date.now()}`,
      at: new Date().toISOString(),
      busPhase,
      graphs,
    };
    this.checkpoints.unshift(cp);
    if (this.checkpoints.length > 20) this.checkpoints.pop();
    this.persistCheckpoints();
    runtimeBus.dispatch({ type: "persistence.checkpoint", domain: "runtime", payload: { id: cp.id } });
    return cp;
  }

  replay(checkpointId?: string): RuntimeCheckpoint | null {
    const cp = checkpointId
      ? this.checkpoints.find((c) => c.id === checkpointId) ?? this.replayLog.find((c) => c.id === checkpointId)
      : this.checkpoints[0] ?? this.replayLog[0];
    if (!cp) return null;
    runtimeBus.dispatch({ type: "persistence.replay", domain: "runtime", payload: { id: cp.id } });
    return cp;
  }

  recover(): RuntimeCheckpoint | null {
    const latest = this.checkpoints[0];
    if (!latest) return null;
    runtimeBus.dispatch({ type: "persistence.recover", domain: "runtime", payload: { id: latest.id } });
    return latest;
  }

  listCheckpoints(): RuntimeCheckpoint[] {
    return [...this.checkpoints];
  }
}

export const runtimePersistence = new RuntimePersistence();
