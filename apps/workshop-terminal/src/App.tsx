import { apiClient, registerTokenStore } from "@zhenhang/http-client";
import {
  queryKeys,
  useBomItemsQuery,
  useQuoteDetailQuery,
  useWorkshopBoardQuery,
} from "@zhenhang/query-hooks";
import { isOnline, useIndustrialRealtimeBridge } from "@zhenhang/realtime";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type CSSProperties } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function setupHttpClient() {
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
}

function groupBomModules(items: Record<string, unknown>[]) {
  const modules = new Map<string, Record<string, unknown>[]>();
  for (const row of items) {
    const code = String(row.item_code ?? "");
    const mod = code.split("-")[0] || "OTHER";
    if (!modules.has(mod)) modules.set(mod, []);
    modules.get(mod)!.push(row);
  }
  return [...modules.entries()].sort(([a], [b]) => a.localeCompare(b));
}

export function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") ?? "");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginPending, setLoginPending] = useState(false);
  const [clock, setClock] = useState(new Date());
  const [online, setOnline] = useState(isOnline());
  const [selectedQuoteId, setSelectedQuoteId] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const boardQuery = useWorkshopBoardQuery(Boolean(token));
  const board = boardQuery.data as Record<string, unknown> | undefined;
  const quoteDetail = useQuoteDetailQuery(selectedQuoteId);
  const detail = quoteDetail.data as Record<string, unknown> | undefined;
  const bomId = detail?.bom_id ? String(detail.bom_id) : null;
  const bomItemsQuery = useBomItemsQuery(bomId);
  const bomItems = ((bomItemsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []);

  useEffect(() => {
    setupHttpClient();
    const t = setInterval(() => setClock(new Date()), 1000);
    const onStatus = () => setOnline(isOnline());
    window.addEventListener("online", onStatus);
    window.addEventListener("offline", onStatus);
    return () => {
      clearInterval(t);
      window.removeEventListener("online", onStatus);
      window.removeEventListener("offline", onStatus);
    };
  }, []);

  useIndustrialRealtimeBridge({
    apiBase: API,
    accessToken: token || null,
    enabled: Boolean(token),
    onEvent: (kind) => {
      if (kind === "workshop.board_refresh" || kind.startsWith("quote.") || kind === "workflow.transition") {
        void queryClient.invalidateQueries({ queryKey: queryKeys.workshop.board() });
        void boardQuery.refetch();
      }
      if (selectedQuoteId && kind.startsWith("quote.")) {
        void quoteDetail.refetch();
      }
    },
    onReconnected: () => {
      void boardQuery.refetch();
      if (selectedQuoteId) void quoteDetail.refetch();
    },
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

  const bomModules = useMemo(() => groupBomModules(bomItems), [bomItems]);

  const login = async () => {
    setLoginError(null);
    setLoginPending(true);
    try {
      const resp = await fetch(`${API}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!resp.ok) {
        setLoginError(resp.status === 401 ? "用户名或密码错误" : `登录失败 (${resp.status})`);
        return;
      }
      const json = await resp.json();
      const access = json?.data?.access_token as string | undefined;
      const refresh = json?.data?.refresh_token as string | undefined;
      if (!access) {
        setLoginError("登录响应无效");
        return;
      }
      localStorage.setItem("access_token", access);
      if (refresh) localStorage.setItem("refresh_token", refresh);
      setupHttpClient();
      setToken(access);
    } catch {
      setLoginError(`无法连接后端 API，请确认 ${API} 已启动`);
    } finally {
      setLoginPending(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken("");
    setSelectedQuoteId(null);
  };

  if (!token) {
    return (
      <main style={{ padding: 48, fontFamily: "monospace", background: "#0f172a", color: "#e2e8f0", minHeight: "100vh" }}>
        <h1 style={{ fontSize: 28 }}>车间数字看板</h1>
        <p style={{ color: "#94a3b8", marginTop: 8 }}>产线状态 · 报价队列 · BOM 只读 · 实时协同</p>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="用户名"
          style={{ display: "block", width: 320, marginTop: 24, padding: 12, fontSize: 16, borderRadius: 8, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0" }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码"
          style={{ display: "block", width: 320, marginTop: 10, padding: 12, fontSize: 16, borderRadius: 8, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0" }}
        />
        {loginError ? <p style={{ color: "#f87171", marginTop: 12 }}>{loginError}</p> : null}
        <button type="button" onClick={login} disabled={loginPending} style={{ marginTop: 20, padding: "14px 40px", fontSize: 18, cursor: "pointer", borderRadius: 8, border: 0, background: "#2563eb", color: "#fff" }}>
          {loginPending ? "登录中…" : "启动终端"}
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
      {!online ? (
        <div style={{ background: "#78350f", color: "#fef3c7", padding: "10px 16px", borderRadius: 8, marginBottom: 16, textAlign: "center", fontSize: 14 }}>
          网络已断开 · 显示缓存数据，恢复后将自动刷新
        </div>
      ) : null}

      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 20, borderBottom: "1px solid #334155", paddingBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700 }}>产线数字看板</h1>
          <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: 13 }}>
            <span style={{ color: online ? "#4ade80" : "#fbbf24" }}>● {online ? "实时协同" : "离线模式"}</span>
            {" · OEE · 设备 · 报警 · BOM 只读"}
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 16 }}>
          <button type="button" onClick={logout} style={{ background: "transparent", border: "1px solid #475569", color: "#94a3b8", padding: "6px 12px", borderRadius: 6, cursor: "pointer", fontSize: 12 }}>
            退出
          </button>
          <div style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
            <div style={{ fontSize: 22, fontWeight: 600 }}>{clock.toLocaleTimeString("zh-CN")}</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>{clock.toLocaleDateString("zh-CN")}</div>
          </div>
        </div>
      </header>

      {boardQuery.isError ? (
        <div style={{ background: "#7f1d1d", padding: 12, borderRadius: 8, marginBottom: 16 }}>看板加载失败，请检查 API 连接</div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        <Kpi label="待审批" value={String(stats.reviewing)} accent="#fbbf24" />
        <Kpi label="已通过" value={String(stats.approved)} accent="#4ade80" />
        <Kpi label="OEE" value={`${stats.oeePct.toFixed(1)}%`} accent="#38bdf8" />
        <Kpi label="报警" value={String(alarms.length)} accent="#f87171" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        <section style={panelStyle}>
          <h2 style={sectionTitle}>报价队列 · 实时</h2>
          {boardQuery.isLoading ? <p style={{ color: "#64748b" }}>加载中…</p> : null}
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
                <tr
                  key={String(q.id)}
                  onClick={() => setSelectedQuoteId(String(q.id))}
                  style={{
                    cursor: "pointer",
                    background: selectedQuoteId === String(q.id) ? "rgba(37,99,235,0.25)" : "transparent",
                  }}
                >
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
          <h2 style={sectionTitle}>产线 · 设备</h2>
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
        </section>
      </div>

      {selectedQuoteId ? (
        <section style={{ ...panelStyle, marginTop: 16, maxHeight: 320 }}>
          <h2 style={sectionTitle}>
            BOM 树（只读）· {String(detail?.quote_no ?? selectedQuoteId)}
          </h2>
          {quoteDetail.isLoading || bomItemsQuery.isLoading ? (
            <p style={{ color: "#64748b" }}>加载 BOM…</p>
          ) : bomModules.length === 0 ? (
            <p style={{ color: "#64748b" }}>该报价无 BOM 物料</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {bomModules.map(([mod, rows]) => (
                <div key={mod} style={{ background: "rgba(15,23,42,0.5)", borderRadius: 8, padding: 10 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8, color: "#38bdf8" }}>{mod}</div>
                  <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11, color: "#cbd5e1" }}>
                    {rows.slice(0, 8).map((r) => (
                      <li key={String(r.item_code)} style={{ marginBottom: 4 }}>
                        {String(r.item_code)} · {String(r.item_name)}
                      </li>
                    ))}
                    {rows.length > 8 ? <li style={{ color: "#64748b" }}>…共 {rows.length} 项</li> : null}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </section>
      ) : null}
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
