"use client";

import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import axios from "axios";
import { registerRefreshHandler, registerTokenStore, type TokenPair } from "@zhenhang/http-client";
import { ThemeProvider } from "next-themes";
import { distributedCoordination } from "@zhenhang/distributed-coordination";
import { distributedRuntime } from "@zhenhang/distributed-runtime";
import { hashSnapshot, runtimeConsistency } from "@zhenhang/runtime-consistency";
import { runtimeBus } from "@zhenhang/runtime-bus";
import { quoteGraph, workflowGraph } from "@zhenhang/runtime-graph";
import { runtimePersistence } from "@zhenhang/runtime-persistence";
import { runtimeScheduler } from "@zhenhang/runtime-scheduler";
import { runtimeStorage } from "@zhenhang/runtime-storage";
import { consensusCoordination } from "@zhenhang/consensus-coordination";
import { runtimeEventStore } from "@zhenhang/runtime-event-store";
import { runtimeFaultTolerance } from "@zhenhang/runtime-fault-tolerance";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";
import { runtimeTransaction } from "@zhenhang/runtime-transaction";
import { telemetryPipeline } from "@zhenhang/telemetry-pipeline";
import { useAuthStore } from "@/store/auth-store";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());
  const bootstrappedRef = React.useRef(false);

  React.useEffect(() => {
    if (bootstrappedRef.current) return;
    bootstrappedRef.current = true;
    runtimeTelemetry.log("info", "runtime.boot", { env: process.env.NODE_ENV });
    runtimeBus.setLifecycle("ready");
    telemetryPipeline.start();
    distributedRuntime.connect();
    const localNode = distributedRuntime.getWorkerId() ?? "local";
    distributedCoordination.join(localNode);
    distributedCoordination.heartbeat(localNode);
    distributedCoordination.electLeader();
    consensusCoordination.startTerm();
    consensusCoordination.vote(localNode, true);
    consensusCoordination.electLeader(localNode);
    const wfSnap = workflowGraph.snapshot("workflow");
    const qSnap = quoteGraph.snapshot("quote");
    const hash = hashSnapshot({ wf: wfSnap, q: qSnap });
    runtimeStorage.saveSnapshot("boot-graphs", { workflow: wfSnap, quote: qSnap });
    const recovered = runtimePersistence.recover();
    if (recovered) {
      runtimeConsistency.validateRecovery(recovered.id, hash);
      runtimeConsistency.replay(0);
    } else {
      const cp = runtimePersistence.checkpoint({ workflow: wfSnap, quote: qSnap }, "ready");
      runtimeConsistency.registerSnapshotVersion(cp.id, hash);
    }
    runtimeBus.registerHook({
      onEvent: (evt) => {
        const eventId = (evt.payload as { event_id?: string })?.event_id ?? `${evt.type}-${evt.at}`;
        const leader = consensusCoordination.getState().leaderId;
        if (leader && !consensusCoordination.isLeader(localNode)) {
          runtimeFaultTolerance.setMode("degraded");
        }
        const tx = runtimeTransaction.begin(["event-store", "consistency"]);
        runtimeTransaction.attachEvent(tx.id, eventId);
        runtimeEventStore.append("runtime", eventId, evt.payload);
        runtimeConsistency.append(eventId, evt.type, evt.payload);
        runtimeConsistency.processOnce(eventId, () => undefined);
        runtimeStorage.appendEvent(eventId, evt);
        void runtimeFaultTolerance.withRetry(
          "event-commit",
          async () => {
            const ok = await runtimeTransaction.prepare(tx.id, [async () => true]);
            if (!ok) throw new Error("Transaction prepare failed");
            await runtimeTransaction.commit(tx.id, [async () => {}]);
            return true;
          },
          () => {
            runtimeTransaction.abort(tx.id);
            return false;
          },
        );
      },
    });

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

  React.useEffect(() => {
    return () => {
      telemetryPipeline.stop();
      distributedRuntime.disconnect();
      runtimePersistence.checkpoint({
        workflow: workflowGraph.snapshot("workflow"),
        quote: quoteGraph.snapshot("quote"),
      }, "shutdown");
      runtimeScheduler.pause();
      runtimeBus.setLifecycle("shutdown");
    };
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ThemeProvider>
  );
}
