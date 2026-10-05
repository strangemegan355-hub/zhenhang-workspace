import { useEffect, useRef } from "react";
import { eventStreamRuntime } from "@zhenhang/event-stream";
import {
  createHeartbeat,
  createReconnectRequest,
  createSubscribeRequest,
  parseEnvelope,
  RealtimeChannel,
  type RealtimeChannelType,
  type RealtimeEnvelope,
} from "@zhenhang/realtime-protocol";

type GatewayOptions = {
  channels: RealtimeChannelType[];
  sseUrl?: string;
  wsUrl?: string;
  heartbeatMs?: number;
  reconnectMs?: number;
  lastEventId?: string;
  onEnvelope?: (envelope: RealtimeEnvelope) => void;
  onMessage?: (channel: RealtimeChannelType, payload: unknown) => void;
  onCursor?: (cursor: { eventId?: string; sequence?: number }) => void;
  onReconnect?: () => void;
};

function parseRaw(raw: string): RealtimeEnvelope | null {
  try {
    const json = JSON.parse(raw);
    return parseEnvelope(json);
  } catch {
    return null;
  }
}

export function useRealtimeGateway(options: GatewayOptions) {
  const reconnectTimer = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const hbRef = useRef<number | null>(null);
  const attemptRef = useRef(0);

  useEffect(() => {
    const reconnectMs = options.reconnectMs ?? 3000;
    const heartbeatMs = options.heartbeatMs ?? 15000;
    let sse: EventSource | null = null;
    let closed = false;

    const dispatch = (envelope: RealtimeEnvelope | null, fallbackChannel: RealtimeChannelType, raw: unknown) => {
      if (envelope) {
        eventStreamRuntime.ingest(envelope);
        options.onEnvelope?.(envelope);
        options.onMessage?.(envelope.channel, envelope.payload);
        return;
      }
      options.onMessage?.(fallbackChannel, raw);
    };

    const subscribeSse = () => {
      if (!options.sseUrl || closed) return;
      sse = new EventSource(options.sseUrl);
      options.channels.forEach((channel) => {
        sse?.addEventListener(channel, (evt) => {
          const message = evt as MessageEvent;
          const envelope = parseRaw(message.data);
          if (message.lastEventId) {
            options.onCursor?.({ eventId: message.lastEventId });
          } else if (envelope?.event_id) {
            options.onCursor?.({
              eventId: envelope.event_id,
              sequence: Number((envelope.meta as Record<string, unknown> | undefined)?.sequence),
            });
          }
          dispatch(envelope, channel, envelope?.payload ?? message.data);
        });
      });
      sse.onopen = () => {
        if (attemptRef.current > 0) options.onReconnect?.();
        attemptRef.current = 0;
      };
      sse.onerror = () => {
        sse?.close();
        attemptRef.current += 1;
        reconnectTimer.current = window.setTimeout(subscribeSse, reconnectMs * attemptRef.current);
      };
    };

    const subscribeWs = () => {
      if (!options.wsUrl || closed) return;
      const ws = new WebSocket(options.wsUrl);
      wsRef.current = ws;
      ws.onopen = () => {
        if (attemptRef.current > 0) options.onReconnect?.();
        attemptRef.current = 0;
        ws.send(JSON.stringify(createReconnectRequest(options.lastEventId, options.channels)));
        ws.send(JSON.stringify(createSubscribeRequest(options.channels)));
        hbRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(createHeartbeat()));
          }
        }, heartbeatMs);
      };
      ws.onmessage = (evt) => {
        const envelope = parseRaw(evt.data);
        const channel = envelope?.channel ?? RealtimeChannel.notification;
        if (envelope?.event_id) {
          options.onCursor?.({
            eventId: envelope.event_id,
            sequence: Number((envelope.meta as Record<string, unknown> | undefined)?.sequence),
          });
        }
        dispatch(envelope, channel, envelope?.payload ?? evt.data);
      };
      ws.onclose = () => {
        if (hbRef.current) window.clearInterval(hbRef.current);
        attemptRef.current += 1;
        reconnectTimer.current = window.setTimeout(subscribeWs, reconnectMs * attemptRef.current);
      };
      ws.onerror = () => ws.close();
    };

    if (options.wsUrl) subscribeWs();
    else subscribeSse();

    return () => {
      closed = true;
      sse?.close();
      wsRef.current?.close();
      if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
      if (hbRef.current) window.clearInterval(hbRef.current);
    };
  }, [options]);
}

export {
  RealtimeChannel,
  createEnvelope,
  createHeartbeat,
  createReconnectRequest,
  createSubscribeRequest,
  parseEnvelope,
} from "@zhenhang/realtime-protocol";
