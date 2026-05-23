export function buildRealtimeUrls(
  apiBase: string,
  accessToken: string,
  opts?: { lastEventId?: string; afterSequence?: number },
) {
  const trimmed = apiBase.replace(/\/$/, "");
  const wsBase = trimmed.replace(/^http/i, (m) => (m.toLowerCase() === "https" ? "wss" : "ws"));
  const params = new URLSearchParams({ token: accessToken });
  if (opts?.lastEventId) params.set("last_event_id", opts.lastEventId);
  if (opts?.afterSequence != null) params.set("after_sequence", String(opts.afterSequence));
  const q = params.toString();
  return {
    wsUrl: `${wsBase}/api/v1/realtime/ws?${q}`,
    sseUrl: `${trimmed}/api/v1/realtime/stream?${q}`,
    replayUrl: `${trimmed}/api/v1/realtime/replay?${q}`,
  };
}
