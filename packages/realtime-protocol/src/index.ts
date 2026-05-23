import { z } from "zod";

/** Protocol version for envelope compatibility. */
export const REALTIME_PROTOCOL_VERSION = "1.0.0" as const;

/** Domain channels — single source of truth for subscriptions. */
export const RealtimeChannel = {
  notification: "notification",
  workflow: "workflow",
  quote: "quote",
  audit: "audit",
} as const;

export type RealtimeChannelType = (typeof RealtimeChannel)[keyof typeof RealtimeChannel];

/** Wire message types. */
export const RealtimeMessageType = {
  event: "event",
  heartbeat: "heartbeat",
  heartbeatAck: "heartbeat_ack",
  subscribe: "subscribe",
  subscribeAck: "subscribe_ack",
  reconnect: "reconnect",
  error: "error",
} as const;

export type RealtimeMessageTypeValue = (typeof RealtimeMessageType)[keyof typeof RealtimeMessageType];

/** Standard message envelope (all realtime payloads). */
export const realtimeEnvelopeSchema = z.object({
  protocol_version: z.string().default(REALTIME_PROTOCOL_VERSION),
  message_type: z.enum([
    RealtimeMessageType.event,
    RealtimeMessageType.heartbeat,
    RealtimeMessageType.heartbeatAck,
    RealtimeMessageType.subscribe,
    RealtimeMessageType.subscribeAck,
    RealtimeMessageType.reconnect,
    RealtimeMessageType.error,
  ]),
  event_version: z.string().default("1"),
  channel: z.enum([
    RealtimeChannel.notification,
    RealtimeChannel.workflow,
    RealtimeChannel.quote,
    RealtimeChannel.audit,
  ]),
  event_id: z.string().optional(),
  timestamp: z.string(),
  payload: z.unknown().optional(),
  meta: z.record(z.string(), z.unknown()).optional(),
});

export type RealtimeEnvelope = z.infer<typeof realtimeEnvelopeSchema>;

export function createEnvelope(
  partial: Pick<RealtimeEnvelope, "message_type" | "channel"> &
    Partial<Omit<RealtimeEnvelope, "message_type" | "channel">>,
): RealtimeEnvelope {
  return realtimeEnvelopeSchema.parse({
    protocol_version: REALTIME_PROTOCOL_VERSION,
    event_version: "1",
    timestamp: new Date().toISOString(),
    ...partial,
  });
}

export function parseEnvelope(raw: unknown): RealtimeEnvelope | null {
  const parsed = realtimeEnvelopeSchema.safeParse(raw);
  return parsed.success ? parsed.data : null;
}

/** Heartbeat protocol — client ping / server ack. */
export function createHeartbeat(): RealtimeEnvelope {
  return createEnvelope({
    message_type: RealtimeMessageType.heartbeat,
    channel: RealtimeChannel.notification,
    payload: { interval_ms: 15000 },
  });
}

export function createHeartbeatAck(refId?: string): RealtimeEnvelope {
  return createEnvelope({
    message_type: RealtimeMessageType.heartbeatAck,
    channel: RealtimeChannel.notification,
    event_id: refId,
    payload: { ok: true },
  });
}

/** Subscribe protocol — channel subscription request. */
export function createSubscribeRequest(channels: RealtimeChannelType[]): RealtimeEnvelope {
  return createEnvelope({
    message_type: RealtimeMessageType.subscribe,
    channel: channels[0] ?? RealtimeChannel.notification,
    payload: { channels },
  });
}

/** Reconnect protocol — resume with last event cursor. */
export function createReconnectRequest(lastEventId?: string, channels?: RealtimeChannelType[]): RealtimeEnvelope {
  return createEnvelope({
    message_type: RealtimeMessageType.reconnect,
    channel: RealtimeChannel.notification,
    event_id: lastEventId,
    payload: { channels: channels ?? Object.values(RealtimeChannel), last_event_id: lastEventId },
  });
}

export function isHeartbeat(envelope: RealtimeEnvelope): boolean {
  return envelope.message_type === RealtimeMessageType.heartbeat;
}

export function isEvent(envelope: RealtimeEnvelope): boolean {
  return envelope.message_type === RealtimeMessageType.event;
}
