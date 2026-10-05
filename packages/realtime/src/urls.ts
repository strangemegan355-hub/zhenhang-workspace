export type RealtimeUrls = {
  wsUrl: string;
  sseUrl: string;
  replayUrl: string;
};

function normalize(apiBase: string): string {
  return apiBase.replace(/\/$/, "");
}

/**
 * Build the realtime transport URLs.
 *
 * The WebSocket and EventSource APIs cannot set request headers, so these transports select
 * the user with a short-lived, realtime-scoped ticket instead of the access token. The ticket
 * is rejected by every header-authenticated endpoint, so a URL that leaks into an access log,
 * a proxy log or browser history cannot be replayed against the REST API.
 *
 * The replay endpoint is an ordinary authenticated GET, so it carries only the cursor and no
 * credential at all: the caller sends its access token in the Authorization header.
 */
export function buildRealtimeUrls(
  apiBase: string,
  ticket: string,
  opts?: { lastEventId?: string; afterSequence?: number },
): RealtimeUrls {
  const trimmed = normalize(apiBase);
  const wsBase = trimmed.replace(/^http/i, (m) => (m.toLowerCase() === "https" ? "wss" : "ws"));

  const cursor = new URLSearchParams();
  if (opts?.lastEventId) cursor.set("last_event_id", opts.lastEventId);
  if (opts?.afterSequence != null) cursor.set("after_sequence", String(opts.afterSequence));
  const cursorQuery = cursor.toString();

  const transport = new URLSearchParams(cursor);
  transport.set("ticket", ticket);

  return {
    wsUrl: `${wsBase}/api/v1/realtime/ws?${transport.toString()}`,
    sseUrl: `${trimmed}/api/v1/realtime/stream?${transport.toString()}`,
    replayUrl: `${trimmed}/api/v1/realtime/replay${cursorQuery ? `?${cursorQuery}` : ""}`,
  };
}

export type RealtimeTicket = { ticket: string; expiresIn: number };

/**
 * Exchange an access token for a short-lived realtime ticket.
 *
 * Called again before each ticket expires so a reconnect always has a usable credential; the
 * access token itself never leaves an Authorization header.
 */
export async function fetchRealtimeTicket(
  apiBase: string,
  accessToken: string,
  signal?: AbortSignal,
): Promise<RealtimeTicket> {
  const resp = await fetch(`${normalize(apiBase)}/api/v1/realtime/ticket`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    signal,
  });
  if (!resp.ok) {
    throw new Error(`realtime ticket request failed with ${resp.status}`);
  }
  const body = (await resp.json()) as
    | { ticket?: string; expires_in?: number; data?: { ticket?: string; expires_in?: number } }
    | null;
  const payload = body?.data ?? body;
  const ticket = payload?.ticket;
  if (!ticket) {
    throw new Error("realtime ticket response did not contain a ticket");
  }
  const expiresIn = Number(payload?.expires_in ?? 300);
  return { ticket, expiresIn: Number.isFinite(expiresIn) && expiresIn > 0 ? expiresIn : 300 };
}
