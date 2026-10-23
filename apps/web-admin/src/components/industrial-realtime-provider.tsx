"use client";

import {
  invalidateByDomain,
  queryKeys,
  useInvalidateQuoteQueries,
} from "@zhenhang/query-hooks";
import { useIndustrialRealtimeBridge } from "@zhenhang/realtime";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useAuthStore } from "@/store/auth-store";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

/** Realtime sync only — no toast popups (user preference for trial UI). */
export function IndustrialRealtimeProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token?.accessToken);
  const queryClient = useQueryClient();
  const invalidateQuotes = useInvalidateQuoteQueries();

  const refreshAll = useCallback(() => {
    invalidateQuotes();
    invalidateByDomain(queryClient, "notifications");
    invalidateByDomain(queryClient, "workflow");
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
    void queryClient.invalidateQueries({ queryKey: queryKeys.workshop.board() });
  }, [invalidateQuotes, queryClient]);

  useIndustrialRealtimeBridge({
    apiBase: API_BASE,
    accessToken: token,
    enabled: Boolean(token),
    onReconnected: refreshAll,
    onEvent: (kind, _channel, payload) => {
      switch (kind) {
        case "notification.new":
          invalidateByDomain(queryClient, "notifications");
          void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
          break;
        case "workflow.transition":
          refreshAll();
          break;
        case "quote.export":
          invalidateQuotes();
          if (payload.task_id) {
            void queryClient.invalidateQueries({
              queryKey: queryKeys.quotes.exportTask(String(payload.task_id)),
            });
          }
          invalidateByDomain(queryClient, "notifications");
          void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
          break;
        case "quote.state_changed":
        case "quote.created":
        case "quote.version_created":
        case "quote.updated":
          invalidateQuotes();
          void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
          break;
        case "dashboard.refresh":
          void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
          break;
        case "workshop.board_refresh":
          void queryClient.invalidateQueries({ queryKey: queryKeys.workshop.board() });
          invalidateQuotes();
          break;
        default:
          break;
      }
    },
  });

  return <>{children}</>;
}
