import { apiClient, registerTokenStore } from "@zhenhang/http-client";
import {
  invalidateByDomain,
  useMarkNotificationReadMutation,
  useNotificationUnreadCountQuery,
  useNotificationsQuery,
  useQuoteTransitionMutation,
  useQuotesQuery,
} from "@zhenhang/query-hooks";
import {
  clearOfflineQueue,
  enqueueOfflineMutation,
  isOnline,
  loadOfflineQueue,
  saveOfflineCache,
  useIndustrialRealtimeBridge,
} from "@zhenhang/realtime";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const styles = {
  app: { fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "0 auto", minHeight: "100vh", background: "#f8fafc" } as const,
  card: { background: "#fff", borderRadius: 12, padding: 14, marginBottom: 10, boxShadow: "0 1px 3px rgba(0,0,0,.08)" } as const,
  primary: { background: "#16a34a", color: "#fff", border: 0, borderRadius: 10, padding: "14px 0", width: "100%", fontSize: 16, fontWeight: 600, cursor: "pointer" } as const,
  danger: { background: "#fff", color: "#dc2626", border: "2px solid #fecaca", borderRadius: 10, padding: "14px 0", width: "100%", fontSize: 16, fontWeight: 600, cursor: "pointer" } as const,
};

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

export function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") ?? "");
  const [tab, setTab] = useState<"quotes" | "notify">("quotes");
  const [selectedQuote, setSelectedQuote] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginPending, setLoginPending] = useState(false);
  const [online, setOnline] = useState(isOnline());

  useEffect(() => {
    setupHttpClient();
    const onStatus = () => setOnline(isOnline());
    window.addEventListener("online", onStatus);
    window.addEventListener("offline", onStatus);
    return () => {
      window.removeEventListener("online", onStatus);
      window.removeEventListener("offline", onStatus);
    };
  }, []);

  const queryClient = useQueryClient();
  const notifications = useNotificationsQuery({ page: 1, unreadOnly: true });
  const unreadQuery = useNotificationUnreadCountQuery();
  const quotes = useQuotesQuery({ page: 1 });

  const flushOffline = async () => {
    const queue = loadOfflineQueue();
    for (const item of queue) {
      if (item.type === "quote.transition" && item.payload.quoteId) {
        await apiClient.post(`/api/v1/quotes/${item.payload.quoteId}/actions/transition`, {
          action_code: item.payload.action_code,
          comment: item.payload.comment,
        });
      }
    }
    clearOfflineQueue();
    await quotes.refetch();
    await notifications.refetch();
    await unreadQuery.refetch();
  };

  useIndustrialRealtimeBridge({
    apiBase: API,
    accessToken: token || null,
    enabled: Boolean(token),
    flushOffline,
    onReconnected: () => {
      void quotes.refetch();
      void notifications.refetch();
      void unreadQuery.refetch();
    },
    onEvent: (kind) => {
      if (kind === "notification.new") {
        invalidateByDomain(queryClient, "notifications");
        void notifications.refetch();
        void unreadQuery.refetch();
      }
      if (
        kind === "workflow.transition" ||
        kind.startsWith("quote.") ||
        kind === "dashboard.refresh"
      ) {
        invalidateByDomain(queryClient, "quotes");
        void quotes.refetch();
      }
    },
  });

  const markRead = useMarkNotificationReadMutation({ page: 1, unreadOnly: true });
  const transition = useQuoteTransitionMutation(selectedQuote ?? "");

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
  };

  if (!token) {
    return (
      <main style={{ ...styles.app, padding: 24 }}>
        <h1 style={{ fontSize: 22 }}>振航 · 移动审批</h1>
        <p style={{ color: "#64748b", fontSize: 14 }}>现场审批报价与通知 · 支持离线队列</p>
        <input
          style={{ display: "block", width: "100%", marginBottom: 10, padding: 12, borderRadius: 8, border: "1px solid #e2e8f0", boxSizing: "border-box" }}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="用户名"
          autoComplete="username"
        />
        <input
          type="password"
          style={{ display: "block", width: "100%", marginBottom: 16, padding: 12, borderRadius: 8, border: "1px solid #e2e8f0", boxSizing: "border-box" }}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码"
          autoComplete="current-password"
        />
        {loginError ? <p style={{ color: "#dc2626", fontSize: 14, marginBottom: 12 }}>{loginError}</p> : null}
        <button type="button" onClick={login} disabled={loginPending} style={{ ...styles.primary, background: "#2563eb", opacity: loginPending ? 0.7 : 1 }}>
          {loginPending ? "登录中…" : "登录"}
        </button>
      </main>
    );
  }

  const quoteItems = ((quotes.data as { items?: Record<string, unknown>[] })?.items ?? []).filter(
    (q) => String(q.workflow_state) === "reviewing",
  );
  const notifyItems = ((notifications.data as { items?: Record<string, unknown>[] })?.items ?? []).slice(0, 15);
  const unreadCount = unreadQuery.data ?? notifyItems.length;
  const offlineQueueLen = loadOfflineQueue().length;

  const doApprove = async (action: "approve" | "reject") => {
    if (!selectedQuote) return;
    if (!isOnline()) {
      enqueueOfflineMutation({
        type: "quote.transition",
        payload: { quoteId: selectedQuote, action_code: action, comment: comment || undefined },
      });
      saveOfflineCache({
        quotes: quotes.data as Record<string, unknown>,
        notifications: notifications.data as Record<string, unknown>,
      });
      alert("已离线保存，联网后自动同步");
      setSelectedQuote(null);
      setComment("");
      return;
    }
    try {
      await transition.mutateAsync({ action_code: action, comment: comment || undefined });
      setSelectedQuote(null);
      setComment("");
      void quotes.refetch();
      void unreadQuery.refetch();
    } catch {
      alert("操作失败，请重试");
    }
  };

  return (
    <main style={{ ...styles.app, paddingBottom: selectedQuote ? 140 : 72 }}>
      {!online ? (
        <div style={{ background: "#fef3c7", color: "#92400e", padding: "8px 12px", fontSize: 13, textAlign: "center" }}>
          网络已断开 · 审批将写入离线队列
        </div>
      ) : null}
      <header style={{ padding: "16px 12px 8px", background: "#fff", borderBottom: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h1 style={{ margin: 0, fontSize: 18 }}>移动业务台</h1>
          <button type="button" onClick={logout} style={{ border: 0, background: "none", color: "#64748b", fontSize: 12, cursor: "pointer" }}>
            退出
          </button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginTop: 10 }}>
          <KpiChip label="待审" value={String(quoteItems.length)} accent="#2563eb" />
          <KpiChip label="未读" value={String(unreadCount)} accent="#f59e0b" />
          <KpiChip label={online ? "在线" : "离线"} value={offlineQueueLen > 0 ? `同步 ${offlineQueueLen}` : "实时"} accent={online ? "#16a34a" : "#f59e0b"} />
        </div>
      </header>
      <nav style={{ display: "flex", gap: 8, padding: 12 }}>
        {(["quotes", "notify"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            style={{
              flex: 1,
              padding: 10,
              borderRadius: 8,
              border: "none",
              background: tab === t ? "#2563eb" : "#e2e8f0",
              color: tab === t ? "#fff" : "#334155",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {t === "quotes" ? "待审报价" : "通知"}
          </button>
        ))}
      </nav>
      <div style={{ padding: "0 12px" }}>
        {tab === "quotes" ? (
          quotes.isLoading ? (
            <p style={{ textAlign: "center", color: "#94a3b8", padding: 32 }}>加载中…</p>
          ) : quotes.isError ? (
            <p style={{ textAlign: "center", color: "#dc2626", padding: 32 }}>加载失败，请检查网络</p>
          ) : quoteItems.length ? (
            quoteItems.map((q) => (
              <button
                key={String(q.id)}
                type="button"
                onClick={() => setSelectedQuote(String(q.id))}
                style={{
                  ...styles.card,
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  cursor: "pointer",
                  border: selectedQuote === String(q.id) ? "2px solid #2563eb" : "1px solid #e2e8f0",
                }}
              >
                <div style={{ fontWeight: 700 }}>{String(q.quote_no)}</div>
                <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>{String(q.title)}</div>
                <div style={{ marginTop: 8, fontSize: 18, fontWeight: 600, color: "#0f172a" }}>
                  ¥{Number(q.total_amount).toLocaleString()}
                </div>
              </button>
            ))
          ) : (
            <p style={{ textAlign: "center", color: "#94a3b8", padding: 32 }}>暂无待审批报价</p>
          )
        ) : notifications.isLoading ? (
          <p style={{ textAlign: "center", color: "#94a3b8", padding: 32 }}>加载中…</p>
        ) : (
          notifyItems.map((n) => (
            <div
              key={String(n.id)}
              style={{ ...styles.card, cursor: "pointer" }}
              onClick={() => markRead.mutate(String(n.id))}
              role="button"
            >
              <div style={{ fontWeight: 600 }}>{String(n.title)}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{String(n.content ?? "").slice(0, 120)}</div>
            </div>
          ))
        )}
      </div>
      {selectedQuote ? (
        <div style={{ position: "fixed", left: 0, right: 0, bottom: 0, maxWidth: 480, margin: "0 auto", padding: 12, background: "#fff", borderTop: "1px solid #e2e8f0", boxShadow: "0 -4px 12px rgba(0,0,0,.06)" }}>
          <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="审批意见（可选）" rows={2} style={{ width: "100%", marginBottom: 8, padding: 10, borderRadius: 8, border: "1px solid #e2e8f0", boxSizing: "border-box" }} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <button type="button" style={styles.primary} onClick={() => doApprove("approve")} disabled={transition.isPending}>
              通过
            </button>
            <button type="button" style={styles.danger} onClick={() => doApprove("reject")} disabled={transition.isPending}>
              拒绝
            </button>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function KpiChip({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div style={{ background: "#f1f5f9", borderRadius: 8, padding: "8px 10px", borderLeft: `3px solid ${accent}` }}>
      <div style={{ fontSize: 10, color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, marginTop: 2 }}>{value}</div>
    </div>
  );
}
