import {
  createEnvelope,
  parseEnvelope,
  RealtimeChannel,
  RealtimeMessageType,
  type RealtimeChannelType,
  type RealtimeEnvelope,
} from "@zhenhang/realtime-protocol";
import { runtimeBus } from "@zhenhang/runtime-bus";

export type StreamName = "notification" | "workflow" | "quote";

const STREAM_CHANNEL: Record<StreamName, RealtimeChannelType> = {
  notification: RealtimeChannel.notification,
  workflow: RealtimeChannel.workflow,
  quote: RealtimeChannel.quote,
};

type Subscriber = (envelope: RealtimeEnvelope) => void;

/** In-memory event stream bus with replay buffer (runtime infrastructure). */
export class EventStreamRuntime {
  private buffer: RealtimeEnvelope[] = [];
  private subscribers = new Map<StreamName, Set<Subscriber>>();
  private maxReplay = 500;

  publish(stream: StreamName, payload: unknown, eventId?: string) {
    const envelope = createEnvelope({
      message_type: RealtimeMessageType.event,
      channel: STREAM_CHANNEL[stream],
      event_id: eventId ?? `evt-${Date.now()}`,
      payload: { stream, data: payload },
    });
    this.buffer.unshift(envelope);
    if (this.buffer.length > this.maxReplay) this.buffer.pop();
    this.subscribers.get(stream)?.forEach((fn) => fn(envelope));
    void runtimeBus.dispatch({ type: `stream.${stream}`, domain: stream, payload: envelope });
    return envelope;
  }

  subscribe(stream: StreamName, handler: Subscriber): () => void {
    if (!this.subscribers.has(stream)) this.subscribers.set(stream, new Set());
    this.subscribers.get(stream)!.add(handler);
    return () => this.subscribers.get(stream)?.delete(handler);
  }

  /** Replay events after cursor (event_id). */
  replay(stream: StreamName, afterEventId?: string): RealtimeEnvelope[] {
    const channel = STREAM_CHANNEL[stream];
    const filtered = this.buffer.filter((e) => e.channel === channel);
    if (!afterEventId) return [...filtered];
    const idx = filtered.findIndex((e) => e.event_id === afterEventId);
    return idx >= 0 ? filtered.slice(0, idx) : [...filtered];
  }

  ingest(raw: unknown) {
    const envelope = typeof raw === "string" ? parseEnvelope(JSON.parse(raw)) : parseEnvelope(raw);
    if (!envelope) return null;
    const stream = (envelope.payload as { stream?: StreamName })?.stream;
    if (stream && stream in STREAM_CHANNEL) {
      this.buffer.unshift(envelope);
      this.subscribers.get(stream)?.forEach((fn) => fn(envelope));
    }
    return envelope;
  }
}

export const eventStreamRuntime = new EventStreamRuntime();

export function subscribeNotificationStream(handler: Subscriber) {
  return eventStreamRuntime.subscribe("notification", handler);
}

export function subscribeWorkflowStream(handler: Subscriber) {
  return eventStreamRuntime.subscribe("workflow", handler);
}

export function subscribeQuoteStream(handler: Subscriber) {
  return eventStreamRuntime.subscribe("quote", handler);
}
