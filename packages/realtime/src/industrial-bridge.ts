import { useEffect, useRef } from "react";
import { useRealtimeGateway } from "@zhenhang/realtime-gateway";
import { loadLastEventId, loadRealtimeCursor, saveRealtimeCursor } from "./cursor-store";
import { isOnline, loadOfflineQueue } from "./offline-store";
import { buildRealtimeUrls } from "./urls";

export type IndustrialEventHandler = (
  kind: string,
  channel: string,
  payload: Record<string, unknown>,
) => void;

function extractCursor(envelope: Record<string, unknown>): { sequence?: number; eventId?: string } {
  const meta = (envelope.meta as Record<string, unknown> | undefined) ?? {};
  const seq = meta.sequence ?? meta.cursor;
  return {
    sequence: seq != null ? Number(seq) : undefined,
    eventId: envelope.event_id ? String(envelope.event_id) : undefined,
  };
}

export function useIndustrialRealtimeBridge(options: {
  apiBase: string;
  accessToken?: string | null;
  enabled?: boolean;
  onEvent: IndustrialEventHandler;
  onReconnected?: () => void;
  flushOffline?: () => Promise<void>;
}) {
  const enabled = options.enabled !== false && Boolean(options.accessToken);
  const cursor = loadRealtimeCursor();
  const lastEventId = cursor?.eventId ?? loadLastEventId();
  const urls =
    enabled && options.accessToken
      ? buildRealtimeUrls(options.apiBase, options.accessToken, {
          lastEventId,
          afterSequence: cursor?.sequence,
        })
      : { wsUrl: undefined, sseUrl: undefined, replayUrl: undefined };

  const flushedRef = useRef(false);

  useEffect(() => {
    if (!enabled || !options.accessToken || !urls.replayUrl) return;
    const ctrl = new AbortController();
    const run = async () => {
      try {
        const resp = await fetch(urls.replayUrl!, {
          headers: { Authorization: `Bearer ${options.accessToken}` },
          signal: ctrl.signal,
        });
        const json = await resp.json();
        const events = (json?.data?.events ?? json?.events ?? []) as Array<Record<string, unknown>>;
        for (const envelope of events) {
          saveRealtimeCursor(extractCursor(envelope));
        }
        if (events.length > 0) {
          options.onReconnected?.();
        }
      } catch {
        /* replay is best-effort on cold start */
      }
    };
    void run();
    return () => ctrl.abort();
  }, [enabled, options.accessToken, urls.replayUrl]);

  useEffect(() => {
    if (!enabled || flushedRef.current) return;
    const flush = async () => {
      if (!isOnline() || !options.flushOffline) return;
      const pending = loadOfflineQueue();
      if (!pending.length) return;
      await options.flushOffline();
      flushedRef.current = true;
      options.onReconnected?.();
    };
    void flush();
    const onOnline = () => {
      flushedRef.current = false;
      void flush();
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [enabled, options.flushOffline]);

  useRealtimeGateway({
    channels: ["notification", "workflow", "quote", "audit"],
    wsUrl: urls.wsUrl,
    sseUrl: urls.sseUrl,
    lastEventId,
    onCursor: (c) => saveRealtimeCursor(c),
    onMessage: (channel, raw) => {
      const envelope =
        raw && typeof raw === "object" ? (raw as Record<string, unknown>) : { payload: raw };
      saveRealtimeCursor(extractCursor(envelope));
      const inner = (
        envelope.payload && typeof envelope.payload === "object"
          ? envelope.payload
          : envelope
      ) as Record<string, unknown>;
      const kind = String(inner.kind ?? envelope.kind ?? "unknown");
      options.onEvent(kind, channel, inner);
    },
    onReconnect: () => options.onReconnected?.(),
  });
}
