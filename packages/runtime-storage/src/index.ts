export type StorageRecord = {
  key: string;
  value: string;
  namespace: string;
  indexedAt: string;
};

export type StorageAdapter = {
  get: (namespace: string, key: string) => string | null;
  set: (namespace: string, key: string, value: string) => void;
  list: (namespace: string) => string[];
  remove: (namespace: string, key: string) => void;
};

function createMemoryAdapter(): StorageAdapter {
  const store = new Map<string, string>();
  const keyOf = (ns: string, k: string) => `${ns}::${k}`;
  return {
    get: (ns, key) => store.get(keyOf(ns, key)) ?? null,
    set: (ns, key, value) => store.set(keyOf(ns, key), value),
    list: (ns) => [...store.keys()].filter((k) => k.startsWith(`${ns}::`)).map((k) => k.split("::")[1]),
    remove: (ns, key) => store.delete(keyOf(ns, key)),
  };
}

/** Runtime storage engine — snapshot / event / graph stores with indexing. */
export class RuntimeStorageEngine {
  private adapter: StorageAdapter;
  private index = new Map<string, StorageRecord>();

  constructor(adapter?: StorageAdapter) {
    this.adapter = adapter ?? createMemoryAdapter();
  }

  private track(namespace: string, key: string, value: string) {
    const record: StorageRecord = {
      key,
      value,
      namespace,
      indexedAt: new Date().toISOString(),
    };
    this.index.set(`${namespace}:${key}`, record);
  }

  // Snapshot store
  saveSnapshot(id: string, data: unknown) {
    const value = JSON.stringify(data);
    this.adapter.set("snapshots", id, value);
    this.track("snapshots", id, value);
  }

  getSnapshot<T = unknown>(id: string): T | null {
    const raw = this.adapter.get("snapshots", id);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  }

  listSnapshots(): string[] {
    return this.adapter.list("snapshots");
  }

  // Event store
  appendEvent(id: string, event: unknown) {
    const value = JSON.stringify(event);
    this.adapter.set("events", id, value);
    this.track("events", id, value);
  }

  getEvent<T = unknown>(id: string): T | null {
    const raw = this.adapter.get("events", id);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  }

  listEvents(): string[] {
    return this.adapter.list("events");
  }

  // Graph store
  saveGraph(id: string, graph: unknown) {
    const value = JSON.stringify(graph);
    this.adapter.set("graphs", id, value);
    this.track("graphs", id, value);
  }

  getGraph<T = unknown>(id: string): T | null {
    const raw = this.adapter.get("graphs", id);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  }

  listGraphs(): string[] {
    return this.adapter.list("graphs");
  }

  /** Runtime index — search by namespace prefix. */
  queryIndex(namespace?: string): StorageRecord[] {
    const all = [...this.index.values()];
    return namespace ? all.filter((r) => r.namespace === namespace) : all;
  }
}

export const runtimeStorage = new RuntimeStorageEngine();
