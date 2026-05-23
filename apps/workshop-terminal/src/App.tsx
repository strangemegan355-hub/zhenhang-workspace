import { apiClient, registerTokenStore } from "@zhenhang/http-client";
import { queryKeys, useWorkshopBoardQuery } from "@zhenhang/query-hooks";
import { useIndustrialRealtimeBridge } from "@zhenhang/realtime";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type CSSProperties } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") ?? "");
  const [clock, setClock] = useState(new Date());
  const queryClient = useQueryClient();
  const boardQuery = useWorkshopBoardQuery(Boolean(token));
  const board = boardQuery.data as Record<string, unknown> | undefined;

  useEffect(() => {
    apiClient.defaults.baseURL = API;
    registerTokenStore({
      getAccessToken: () => localStorage.getItem("access_token") ?? undefined,
      getRefreshToken: () => localStorage.getItem("refresh_token") ?? undefined,
      setTokens: ({ accessToken, refreshToken }) => {
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
      },
      clearTokens: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      },
    });
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useIndustrialRealtimeBridge({
    apiBase: API,
    accessToken: token || null,
    enabled: Boolean(token),
    onEvent: (kind) => {
      if (kind === "workshop.board_refresh" || kind.startsWith("quote.") || kind === "workflow.transition") {
        void queryClient.invalidateQueries({ queryKey: queryKeys.workshop.board() });
        boardQuery.refetch();
      }
    },
    onReconnected: () => boardQuery.refetch(),
  });

  const liveQuotes = (board?.live_quotes as Array<Record<string, unknown>>) ?? [];
  const equipment = (board?.equipment as Array<Record<string, unknown>>) ?? [];
  const alarms = (board?.alarms as Array<Record<string, unknown>>) ?? [];
  const oee = (board?.oee as Record<string, unknown>) ?? {};
  const production = (board?.production as Record<string, unknown>) ?? {};
  const lines = (production.lines as Array<Record<string, unknown>>) ?? [];

  const stats = useMemo(() => {
    const pipeline = (production.quote_pipeline as Array<{ state: string; count: number }>) ?? [];
    const reviewing = pipeline.find((p) => p.state === "reviewing")?.count ?? 0;
    const approved = pipeline.find((p) => p.state === "approved")?.count ?? 0;
    return { reviewing, approved, oeePct: Number(oee.oee ?? 0) * 100 };
  }, [production, oee]);

  const login = async () => {
    const resp = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "admin", password: "Admin@123456" }),
    });
    const json = await resp.json();
    const access = json?.data?.access_token as string | undefined;
    if (access) {
      localStorage.setItem("access_token", access);
      setToken(access);
    }
  };

  if (!token) {
    return (
      <main style={{ padding: 48, fontFamily: "monospace", background: "#0f172a", color: "#e2e8f0", minHeight: "100vh" }}>
        <h1 style={{ fontSize: 28 }}>车间数字看板</h1>
        <button type="button" onClick={login} style={{ marginTop: 24, padding: "16px 40px", fontSize: 18, cursor: "pointer" }}>
          启动终端
        </button>
      </main>
    );
  }

  const alarmColor: Record<string, string> = {
    critical: "#f87171",
    warning: "#fbbf24",
    info: "#38bdf8",
  };

  return (
    <main
      style={{
        padding: 20,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
        color: "#e2e8f0",
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20, borderBottom: "1px solid #334155", paddingBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700 }}>产线数字看板</h1>
          <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: 13 }}>
            <span style={{ color: "#4ade80" }}>● 实时协同</span> · OEE 基础 · 设备 · 报警
          </p>
        </div>
        <div style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          <div style={{ fontSize: 22, fontWeight: 600 }}>{clock.toLocaleTimeString("zh-CN")}</div>
          <div style={{ fontSize: 12, color: "#64748b" }}>{clock.toLocaleDateString("zh-CN")}</div>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        <Kpi label="待审批" value={String(stats.reviewing)} accent="#fbbf24" />
        <Kpi label="已通过" value={String(stats.approved)} accent="#4ade80" />
        <Kpi label="OEE" value={`${stats.oeePct.toFixed(1)}%`} accent="#38bdf8" />
        <Kpi label="报警" value={String(alarms.length)} accent="#f87171" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr 0.9fr", gap: 16 }}>
        <section style={panelStyle}>
          <h2 style={sectionTitle}>报价队列 · 实时</h2>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: "#64748b", fontSize: 11 }}>
                <th align="left">单号</th>
                <th align="left">状态</th>
                <th align="right">金额</th>
              </tr>
            </thead>
            <tbody>
              {liveQuotes.map((q) => (
                <tr key={String(q.id)}>
                  <td style={{ padding: "8px 4px", fontWeight: 600 }}>{String(q.quote_no)}</td>
                  <td style={{ padding: "8px 4px" }}>{String(q.workflow_state)}</td>
                  <td align="right" style={{ padding: "8px 4px" }}>
                    {Number(q.total_amount ?? 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section style={panelStyle}>
          <h2 style={sectionTitle}>产线状态</h2>
          {lines.map((line) => (
            <div key={String(line.line_id)} style={{ marginBottom: 10, padding: 10, background: "rgba(15,23,42,0.5)", borderRadius: 8 }}>
              <div style={{ fontWeight: 700 }}>{String(line.name)}</div>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>
                状态 {String(line.state)} · WIP {String(line.wip_quotes)}
              </div>
            </div>
          ))}
          <h3 style={{ ...sectionTitle, marginTop: 16 }}>设备状态</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {equipment.map((eq) => (
              <div key={String(eq.id)} style={{ fontSize: 12, padding: 8, border: "1px solid #334155", borderRadius: 6 }}>
                <div style={{ fontWeight: 600 }}>{String(eq.code)}</div>
                <div style={{ color: "#94a3b8" }}>{String(eq.status)}</div>
              </div>
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={sectionTitle}>工业报警</h2>
          {alarms.length === 0 ? (
            <p style={{ color: "#64748b", fontSize: 13 }}>当前无活跃报警</p>
          ) : (
            alarms.map((a) => (
              <div
                key={`${a.code}-${a.at}`}
                style={{
                  marginBottom: 8,
                  padding: 10,
                  borderLeft: `4px solid ${alarmColor[String(a.level)] ?? "#fff"}`,
                  background: "rgba(15,23,42,0.6)",
                  fontSize: 12,
                }}
              >
                <div style={{ fontWeight: 700, color: alarmColor[String(a.level)] }}>{String(a.code)}</div>
                <div>{String(a.message)}</div>
              </div>
            ))
          )}
          <p style={{ marginTop: 12, fontSize: 10, color: "#64748b" }}>{String(oee.foundation_note ?? "")}</p>
        </section>
      </div>
    </main>
  );
}

const panelStyle: CSSProperties = {
  background: "rgba(30,41,59,0.8)",
  borderRadius: 12,
  padding: 16,
  border: "1px solid #334155",
  maxHeight: 480,
  overflow: "auto",
};

const sectionTitle: CSSProperties = {
  margin: "0 0 12px",
  fontSize: 13,
  color: "#94a3b8",
  textTransform: "uppercase",
  letterSpacing: 2,
};

function Kpi({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div style={{ background: "rgba(30,41,59,0.9)", borderRadius: 10, padding: 14, borderLeft: `4px solid ${accent}` }}>
      <div style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, marginTop: 4 }}>{value}</div>
    </div>
  );
}
