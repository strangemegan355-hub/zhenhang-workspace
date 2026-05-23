const CURSOR_KEY = "zhenhang.realtime.cursor";
const EVENT_ID_KEY = "zhenhang.realtime.last_event_id";

export type RealtimeCursor = {
  sequence?: number;
  eventId?: string;
  updatedAt: string;
};

export function loadRealtimeCursor(): RealtimeCursor | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(CURSOR_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as RealtimeCursor;
  } catch {
    return null;
  }
}

export function saveRealtimeCursor(cursor: { sequence?: number; eventId?: string }) {
  if (typeof localStorage === "undefined") return;
  const payload: RealtimeCursor = {
    sequence: cursor.sequence,
    eventId: cursor.eventId,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(CURSOR_KEY, JSON.stringify(payload));
  if (cursor.eventId) {
    localStorage.setItem(EVENT_ID_KEY, cursor.eventId);
  }
  if (cursor.sequence != null) {
    localStorage.setItem(`${CURSOR_KEY}.seq`, String(cursor.sequence));
  }
}

export function loadLastEventId(): string | undefined {
  if (typeof localStorage === "undefined") return undefined;
  return localStorage.getItem(EVENT_ID_KEY) ?? undefined;
}
