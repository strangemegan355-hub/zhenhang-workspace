"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { healthFromErrorRate, healthFromLatency, type ServiceHealth } from "./dashboard-utils";

type ReadySnap = { db?: { status?: string; latency_ms?: number }; redis?: { status?: string; latency_ms?: number } };
type MetricsSnap = { api?: { error_rate?: number }; realtime?: { ws_connections_active?: number; sse_connections_active?: number }; worker?: { queue_backlog_pending?: number } };
type ServiceRow = { key: string; label: string; health: ServiceHealth; detail: string };

const HEALTH_DOT: Record<ServiceHealth, string> = { healthy: "bg-[var(--color-success)]", warning: "bg-[var(--color-warning)] animate-pulse", error: "bg-[var(--color-danger)] animate-pulse" };
const HEALTH_LABEL: Record<ServiceHealth, string> = { healthy: "正常", warning: "警告", error: "异常" };

export function SystemStatusCard({ metrics, token }: { metrics?: MetricsSnap | null; token?: string | null }) {
  const [ready, setReady] = useState<ReadySnap | null>(null);
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await fetch(`\${apiBase}/api/v1/health/ready`);
        if (!resp.ok) return;
        const json = await resp.json();
        if (!cancelled) setReady((json?.data ?? json) as ReadySnap);
      } catch { /* optional */ }
    };
    void load();
    const id = window.setInterval(() => void load(), 60000);
    return () => { cancelled = true; window.clearInterval(id); };
  }, [token]);

  const errorRate = metrics?.api?.error_rate ?? 0;
  const wsConnections = (metrics?.realtime?.ws_connections_active ?? 0) + (metrics?.realtime?.sse_connections_active ?? 0);
  const workerBacklog = metrics?.worker?.queue_backlog_pending ?? 0;
  const apiHealth = healthFromErrorRate(errorRate);
  const pgHealth = ready?.db?.status === "up" ? healthFromLatency(ready.db.latency_ms) : ("warning" as const);
  const redisHealth = ready?.redis?.status === "up" ? healthFromLatency(ready.redis.latency_ms) : ("warning" as const);
  const wsHealth: ServiceHealth = wsConnections > 0 ? "healthy" : token ? "warning" : "healthy";
  const workerHealth: ServiceHealth = workerBacklog > 50 ? "error" : workerBacklog > 10 ? "warning" : "healthy";
  const minioHealth: ServiceHealth = apiHealth === "error" ? "warning" : "healthy";

  const services: ServiceRow[] = [
    { key: "api", label: "API", health: apiHealth, detail: errorRate < 0.05 ? "响应正常" : `错误率 \${(errorRate * 100).toFixed(1)}%` },
    { key: "postgres", label: "PostgreSQL", health: pgHealth, detail: ready?.db?.latency_ms != null ? `\${ready.db.latency_ms} ms` : "检测中" },
    { key: "redis", label: "Redis", health: redisHealth, detail: ready?.redis?.latency_ms != null ? `\${ready.redis.latency_ms} ms` : "检测中" },
    { key: "minio", label: "MinIO", health: minioHealth, detail: "对象存储" },
    { key: "worker", label: "Worker", health: workerHealth, detail: workerBacklog > 0 ? `队列 \${workerBacklog}` : "空闲" },
    { key: "websocket", label: "WebSocket", health: wsHealth, detail: `\${wsConnections} 连接` },
  ];

  return (
    <DashboardCard title="系统状态" toolbar={<span className="flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]"><RefreshCw className="h-3 w-3" />60s 刷新</span>}>
      <div className="grid gap-2 sm:grid-cols-2">
        {services.map((svc) => (
          <div key={svc.key} className="flex items-center gap-3 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2.5">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full \${HEALTH_DOT[svc.health]}`} />
            <div className="min-w-0 flex-1"><p className="text-xs font-medium text-[var(--color-text)]">{svc.label}</p><p className="text-[11px] text-[var(--color-text-muted)]">{svc.detail}</p></div>
            <span className={`shrink-0 text-[10px] font-semibold \${svc.health === "healthy" ? "text-[var(--color-success)]" : svc.health === "warning" ? "text-[var(--color-warning)]" : "text-[var(--color-danger)]"}`}>{HEALTH_LABEL[svc.health]}</span>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
