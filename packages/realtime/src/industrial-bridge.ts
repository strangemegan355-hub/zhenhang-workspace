import { useEffect, useMemo, useRef, useState } from "react";
import { useRealtimeGateway } from "@zhenhang/realtime-gateway";
import { loadLastEventId, loadRealtimeCursor, saveRealtimeCursor } from "./cursor-store";
import { isOnline, loadOfflineQueue } from "./offline-store";
import { buildRealtimeUrls, fetchRealtimeTicket, type RealtimeTicket } from "./urls";

export type IndustrialEventHandler = (
  kind: string,
  channel: string,
  payload: Record<string, unknown>,
) => void;

const CHANNELS = ["notification", "workflow", "quote", "audit"] as const;
const TICKET_RETRY_MS = 15_000;
const TICKET_MIN_REFRESH_MS = 30_000;

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
  const afterSequence = cursor?.sequence;

  // Callbacks live in refs so the gateway options stay referentially stable: the gateway
  // restarts its transport whenever its options object changes, and inline props from the
  // apps would otherwise reconnect the socket on every render.
  const onEventRef = useRef(options.onEvent);
  const onReconnectedRef = useRef(options.onReconnected);

  // Copied in an effect rather than during render: mutating a ref while rendering is what the React
  // Compiler flags. The transport reads these only when an event arrives, which is after the commit.
  useEffect(() => {
    onEventRef.current = options.onEvent;
    onReconnectedRef.current = options.onReconnected;
  }, [options.onEvent, options.onReconnected]);

  const [ticketState, setTicketState] = useState<{ token: string; ticket: RealtimeTicket } | null>(
    null,
  );
  // Derived rather than cleared by the effect: a ticket issued for a different access token must not be
  // used, and clearing state synchronously inside an effect is what the React Compiler flags.
  const ticket = ticketState && ticketState.token === options.accessToken ? ticketState.ticket : null;

  // A URL cannot carry the access token safely, so the transport credential is a short-lived
  // ticket that is re-issued before it expires. Refreshing it changes the URL below, which is
  // what makes the gateway reconnect with a fresh, valid credential instead of a stale one.
  useEffect(() => {
    if (!enabled || !options.accessToken) {
      return;
    }
    let cancelled = false;
    let timer: number | null = null;
    const ctrl = new AbortController();

    const load = async () => {
      try {
        const next = await fetchRealtimeTicket(options.apiBase, options.accessToken as string, ctrl.signal);
        if (cancelled) return;
        setTicketState({ token: options.accessToken as string, ticket: next });
        const refreshIn = Math.max(TICKET_MIN_REFRESH_MS, (next.expiresIn - 30) * 1000);
        timer = window.setTimeout(() => void load(), refreshIn);
      } catch {
        if (cancelled) return;
        // Keep the current ticket: a failed refresh must not tear down a working transport.
        timer = window.setTimeout(() => void load(), TICKET_RETRY_MS);
      }
    };

    void load();
    return () => {
      cancelled = true;
      ctrl.abort();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, options.accessToken, options.apiBase]);

  const urls = useMemo(() => {
    if (!enabled || !ticket) {
      return { wsUrl: undefined, sseUrl: undefined, replayUrl: undefined };
    }
    return buildRealtimeUrls(options.apiBase, ticket.ticket, { lastEventId, afterSequence });
    // afterSequence/lastEventId are read once per ticket so a refresh cannot reorder them.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ticket, options.apiBase]);

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
          onReconnectedRef.current?.();
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
      onReconnectedRef.current?.();
    };
    void flush();
    const onOnline = () => {
      flushedRef.current = false;
      void flush();
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
    // The effect must not depend on the `options` object: its identity changes every render and the
    // file's own comment explains why the transport must not restart with it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, options.flushOffline]);

  const gatewayOptions = useMemo(
    () => ({
      channels: [...CHANNELS],
      wsUrl: urls.wsUrl,
      sseUrl: urls.sseUrl,
      lastEventId,
      onCursor: (c: { eventId?: string; sequence?: number }) => saveRealtimeCursor(c),
      onMessage: (channel: (typeof CHANNELS)[number], raw: unknown) => {
        const envelope =
          raw && typeof raw === "object" ? (raw as Record<string, unknown>) : { payload: raw };
        saveRealtimeCursor(extractCursor(envelope));
        const inner = (
          envelope.payload && typeof envelope.payload === "object" ? envelope.payload : envelope
        ) as Record<string, unknown>;
        const kind = String(inner.kind ?? envelope.kind ?? "unknown");
        onEventRef.current(kind, channel, inner);
      },
      onReconnect: () => onReconnectedRef.current?.(),
    }),
    [urls.wsUrl, urls.sseUrl, lastEventId],
  );

  useRealtimeGateway(gatewayOptions);
}
