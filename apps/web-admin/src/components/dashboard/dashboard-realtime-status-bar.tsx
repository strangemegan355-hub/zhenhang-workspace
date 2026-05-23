"use client";

import { isOnline, loadRealtimeCursor } from "@zhenhang/realtime";
import { RealtimeDot, designTokens, typography } from "@zhenhang/ui";
import type { RealtimeDotLevel } from "@zhenhang/ui";
import { useAuthStore } from "@/store/auth-store";
import { useEffect, useState, useSyncExternalStore } from "react";

type HealthMetrics = {
  worker?: { failures_total?: number; queue_backlog_pending?: number; queue_backlog_dead_letter?: number };
};

function subscribeOnline(onStoreChange: () => void) {
  window.addEventListener("online", onStoreChange);
  window.addEventListener("offline", onStoreChange);
  return () => {
    window.removeEventListener("online", onStoreChange);
    window.removeEventListener("offline", onStoreChange);
  };
}

function getOnlineSnapshot() {
  return isOnline();
}

export function DashboardRealtimeStatusBar({
  exportPending = 0,
}: {
  exportPending?: number;
}) {
  const token = useAuthStore((s) => s.token?.accessToken);
  const online = useSyncExternalStore(subscribeOnline, getOnlineSnapshot, () => true);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [tickNow, setTickNow] = useState(0);
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);

  useEffect(() => {
    const tick = () => {
      const cursor = loadRealtimeCursor();
      setLastSync(cursor?.updatedAt ?? null);
      setTickNow(Date.now());
    };
    const initial = window.setTimeout(tick, 0);
    const interval = window.setInterval(tick, 5000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!token) return;
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    let cancelled = false;

    const load = async () => {
      try {
        const resp = await fetch(`${apiBase}/api/v1/health/metrics`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!resp.ok) return;
        const json = await resp.json();
        const data = (json?.data ?? json) as HealthMetrics;
        if (!cancelled) setMetrics(data);
      } catch {
        /* optional */
      }
    };

    void load();
    const interval = window.setInterval(() => void load(), 30000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [token]);

  const hasToken = Boolean(token);
  const cursorFresh =
    tickNow > 0 &&
    lastSync != null &&
    tickNow - new Date(lastSync).getTime() < 5 * 60 * 1000;
  const realtimeLevel: RealtimeDotLevel = !hasToken
    ? "idle"
    : !online
      ? "error"
      : cursorFresh || online
        ? "ok"
        : "warn";

  const workerFailures = metrics?.worker?.failures_total ?? 0;
  const workerLevel: RealtimeDotLevel =
    workerFailures > 5 ? "error" : workerFailures > 0 ? "warn" : hasToken ? "ok" : "idle";

  const queuePending = metrics?.worker?.queue_backlog_pending ?? exportPending;
  const queueDead = metrics?.worker?.queue_backlog_dead_letter ?? 0;
  const queueLevel: RealtimeDotLevel =
    queueDead > 0 ? "error" : queuePending > 0 ? "warn" : "ok";

  const syncLabel = lastSync
    ? lastSync.replace("T", " ").slice(0, 19)
    : hasToken
      ? "等待首条事件"
      : "未登录";

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 rounded border px-4 py-2"
      style={{
        backgroundColor: designTokens.colors.background.elevated,
        borderColor: designTokens.colors.border.default,
      }}
    >
      <div className="flex flex-wrap items-center gap-4">
        <RealtimeDot
          level={realtimeLevel}
          pulse={realtimeLevel === "warn"}
          label={
            realtimeLevel === "ok"
              ? "realtime connected"
              : realtimeLevel === "warn"
                ? "realtime reconnecting"
                : realtimeLevel === "error"
                  ? "realtime offline"
                  : "realtime idle"
          }
        />
        <RealtimeDot
          level={workerLevel}
          label={
            workerLevel === "ok"
              ? "worker healthy"
              : workerLevel === "warn"
                ? "worker degraded"
                : workerLevel === "error"
                  ? "worker errors"
                  : "worker unknown"
          }
        />
        <RealtimeDot
          level={queueLevel}
          label={queueLevel === "ok" ? "queue healthy" : queueLevel === "error" ? "queue dead-letter" : "queue backlog"}
        />
      </div>
      <span className={typography.caption} style={{ color: designTokens.colors.text.muted }}>
        last sync · {syncLabel}
      </span>
    </div>
  );
}
