"use client";

import {
  invalidateByDomain,
  queryKeys,
  useInvalidateQuoteQueries,
} from "@zhenhang/query-hooks";
import { useIndustrialRealtimeBridge, useToastStore } from "@zhenhang/realtime";
import { useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { useAuthStore } from "@/store/auth-store";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function IndustrialRealtimeProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token?.accessToken);
  const queryClient = useQueryClient();
  const invalidateQuotes = useInvalidateQuoteQueries();
  const push = useToastStore((s) => s.push);
  const seq = useRef(0);

  useIndustrialRealtimeBridge({
    apiBase: API_BASE,
    accessToken: token,
    onEvent: (kind, _channel, payload) => {
      seq.current += 1;
      const id = `rt-${seq.current}`;

      switch (kind) {
        case "notification.new":
          push({
            id,
            title: String(payload.title ?? "新通知"),
            description: "消息中心已同步",
          });
          invalidateByDomain(queryClient, "notifications");
          break;
        case "workflow.transition":
          push({
            id,
            title: "审批状态更新",
            description: `${payload.quote_no ?? ""} · ${payload.from_state} → ${payload.to_state}`,
          });
          invalidateQuotes();
          invalidateByDomain(queryClient, "workflow");
          break;
        case "quote.export": {
          const status = String(payload.status ?? "");
          push({
            id,
            title: status === "completed" ? "导出完成" : "导出进度",
            description: `${payload.quote_no ?? ""} · ${status}`,
          });
          invalidateQuotes();
          if (payload.task_id) {
            void queryClient.invalidateQueries({
              queryKey: queryKeys.quotes.exportTask(String(payload.task_id)),
            });
          }
          invalidateByDomain(queryClient, "notifications");
          break;
        }
        case "quote.state_changed":
        case "quote.created":
        case "quote.version_created":
        case "quote.updated":
          invalidateQuotes();
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
