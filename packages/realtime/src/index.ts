import { useEffect } from "react";
import { create } from "zustand";

export type ToastMessage = { id: string; title: string; description?: string };

/** Callers may supply their own id; one is generated when they do not. */
export type ToastInput = { id?: string; title: string; description?: string };

type ToastState = {
  messages: ToastMessage[];
  push: (msg: ToastInput) => void;
  remove: (id: string) => void;
};

function makeToastId(): string {
  return `toast-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export const useToastStore = create<ToastState>((set) => ({
  messages: [],
  push: (msg) => set((s) => ({ messages: [{ ...msg, id: msg.id ?? makeToastId() }, ...s.messages].slice(0, 5) })),
  remove: (id) => set((s) => ({ messages: s.messages.filter((m) => m.id !== id) })),
}));

export { buildRealtimeUrls } from "./urls";
export { useIndustrialRealtimeBridge } from "./industrial-bridge";
export type { IndustrialEventHandler } from "./industrial-bridge";
export {
  loadRealtimeCursor,
  saveRealtimeCursor,
  loadLastEventId,
} from "./cursor-store";
export {
  isOnline,
  loadOfflineQueue,
  enqueueOfflineMutation,
  clearOfflineQueue,
  saveOfflineCache,
  loadOfflineCache,
} from "./offline-store";
export type { OfflineMutation, OfflineCacheInput, OfflineCacheSnapshot } from "./offline-store";

export function useNotificationRealtime(options?: { sseUrl?: string; onMessage?: (data: unknown) => void }) {
  useEffect(() => {
    if (!options?.sseUrl) return;
    const source = new EventSource(options.sseUrl);
    source.onmessage = (evt) => {
      let parsed: unknown = evt.data;
      try {
        parsed = JSON.parse(evt.data);
      } catch {
        parsed = evt.data;
      }
      options.onMessage?.(parsed);
    };
    return () => source.close();
  }, [options]);
}
