import { useEffect } from "react";
import { create } from "zustand";

export type ToastMessage = { id: string; title: string; description?: string };

type ToastState = {
  messages: ToastMessage[];
  push: (msg: ToastMessage) => void;
  remove: (id: string) => void;
};

export const useToastStore = create<ToastState>((set) => ({
  messages: [],
  push: (msg) => set((s) => ({ messages: [msg, ...s.messages].slice(0, 5) })),
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
export type { OfflineMutation, OfflineCacheSnapshot } from "./offline-store";

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
