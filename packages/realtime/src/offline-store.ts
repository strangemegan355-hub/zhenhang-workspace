const OFFLINE_QUEUE_KEY = "zhenhang.offline.queue";
const OFFLINE_CACHE_KEY = "zhenhang.offline.cache";

export type OfflineMutation = {
  id: string;
  type: "quote.transition" | "notification.read";
  payload: Record<string, unknown>;
  createdAt: string;
};

export type OfflineCacheSnapshot = {
  quotes?: Record<string, unknown>;
  notifications?: Record<string, unknown>;
  updatedAt: string;
};

export function isOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine;
}

export function loadOfflineQueue(): OfflineMutation[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    return raw ? (JSON.parse(raw) as OfflineMutation[]) : [];
  } catch {
    return [];
  }
}

export function enqueueOfflineMutation(item: Omit<OfflineMutation, "id" | "createdAt">) {
  const queue = loadOfflineQueue();
  queue.push({
    ...item,
    id: `off-${Date.now()}-${queue.length}`,
    createdAt: new Date().toISOString(),
  });
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue.slice(-50)));
}

export function clearOfflineQueue() {
  localStorage.removeItem(OFFLINE_QUEUE_KEY);
}

export function saveOfflineCache(snapshot: OfflineCacheSnapshot) {
  localStorage.setItem(
    OFFLINE_CACHE_KEY,
    JSON.stringify({ ...snapshot, updatedAt: new Date().toISOString() }),
  );
}

export function loadOfflineCache(): OfflineCacheSnapshot | null {
  try {
    const raw = localStorage.getItem(OFFLINE_CACHE_KEY);
    return raw ? (JSON.parse(raw) as OfflineCacheSnapshot) : null;
  } catch {
    return null;
  }
}
