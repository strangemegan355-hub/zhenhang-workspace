"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { registerRefreshHandler, registerTokenStore, type TokenPair } from "@zhenhang/http-client";
import axios from "axios";
import { ThemeProvider } from "next-themes";
import * as React from "react";
import { useAuthStore } from "@/store/auth-store";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());
  const bootstrappedRef = React.useRef(false);

  React.useEffect(() => {
    if (bootstrappedRef.current) return;
    bootstrappedRef.current = true;

    // This provider owns exactly two pieces of real wiring: where the HTTP client reads its tokens
    // from, and how it refreshes them.
    //
    // It previously booted a simulated distributed runtime on startup: it "connected" a cluster,
    // joined a node, sent heartbeats, started a consensus term, voted for itself, elected a local
    // leader, snapshotted two state graphs, wrote a checkpoint to browser storage and registered a
    // bus hook that opened a transaction and appended to an event store for every realtime event.
    // All of it ran in one browser tab against no server, so the "cluster", the election and the
    // transactions were fabricated, and any operator reading the dev-tools panel was reading
    // invented state. Real infrastructure belongs in the backend; the front end now boots nothing.
    registerTokenStore({
      getAccessToken: () => useAuthStore.getState().token?.accessToken,
      getRefreshToken: () => useAuthStore.getState().token?.refreshToken,
      setTokens: (tokens: TokenPair) => useAuthStore.getState().setTokens(tokens),
      clearTokens: () => useAuthStore.getState().clearSession(),
    });

    registerRefreshHandler(async () => {
      const refreshToken = useAuthStore.getState().token?.refreshToken;
      if (!refreshToken) return null;
      const resp = await axios.post<{ code: string; data: { access_token: string; refresh_token: string } }>(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/auth/refresh`,
        { refresh_token: refreshToken },
      );
      return {
        accessToken: resp.data.data.access_token,
        refreshToken: resp.data.data.refresh_token,
      };
    });
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}
