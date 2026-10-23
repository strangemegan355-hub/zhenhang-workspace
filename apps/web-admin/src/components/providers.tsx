"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { apiClient, registerRefreshHandler, registerTokenStore, type TokenPair } from "@zhenhang/http-client";
import axios from "axios";
import { ThemeProvider } from "next-themes";
import * as React from "react";
import { useAuthStore } from "@/store/auth-store";

// Empty string is intentional for prod (same-origin via nginx). Only fall back when unset.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : "http://127.0.0.1:8000";

// Register before any child queryFn runs. useEffect is too late: the first React Query
// fetch can start during commit, while effects still have not run — leaving baseURL/token
// unset and hanging relative requests against the Next origin.
apiClient.defaults.baseURL = API_BASE;

function tokenFromPersistStorage(kind: "accessToken" | "refreshToken"): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const raw = window.localStorage.getItem("zhenhang-web-admin-auth");
    if (!raw) return undefined;
    const parsed = JSON.parse(raw) as { state?: { token?: TokenPair } };
    return parsed.state?.token?.[kind];
  } catch {
    return undefined;
  }
}

registerTokenStore({
  // Prefer live zustand state; fall back to localStorage for the first paint before persist rehydrates.
  getAccessToken: () => useAuthStore.getState().token?.accessToken ?? tokenFromPersistStorage("accessToken"),
  getRefreshToken: () => useAuthStore.getState().token?.refreshToken ?? tokenFromPersistStorage("refreshToken"),
  setTokens: (tokens: TokenPair) => useAuthStore.getState().setTokens(tokens),
  clearTokens: () => useAuthStore.getState().clearSession(),
});
registerRefreshHandler(async () => {
  const refreshToken = useAuthStore.getState().token?.refreshToken;
  if (!refreshToken) return null;
  const resp = await axios.post<{ code: string; data: { access_token: string; refresh_token: string } }>(
    `${API_BASE}/api/v1/auth/refresh`,
    { refresh_token: refreshToken },
  );
  return {
    accessToken: resp.data.data.access_token,
    refreshToken: resp.data.data.refresh_token,
  };
});

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}
