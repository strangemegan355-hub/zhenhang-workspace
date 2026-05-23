"use client";

import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { eventStreamRuntime } from "@zhenhang/event-stream";
import { runtimeBus } from "@zhenhang/runtime-bus";
import { quoteGraph, workflowGraph } from "@zhenhang/runtime-graph";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";
import { agentGovernance } from "@zhenhang/agent-governance";
import { distributedCoordination } from "@zhenhang/distributed-coordination";
import { distributedRuntime } from "@zhenhang/distributed-runtime";
import { runtimeConsistency } from "@zhenhang/runtime-consistency";
import { runtimeSecurity } from "@zhenhang/runtime-security";
import { runtimeStorage } from "@zhenhang/runtime-storage";
import { runtimePersistence } from "@zhenhang/runtime-persistence";
import { runtimeScheduler } from "@zhenhang/runtime-scheduler";
import { telemetryPipeline } from "@zhenhang/telemetry-pipeline";
import { consensusCoordination } from "@zhenhang/consensus-coordination";
import { runtimeEventStore } from "@zhenhang/runtime-event-store";
import { runtimeFaultTolerance } from "@zhenhang/runtime-fault-tolerance";
import { runtimeTransaction } from "@zhenhang/runtime-transaction";
import { agentPolicyEngine } from "@zhenhang/agent-policy-engine";

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded border p-2 text-xs dark:border-zinc-700">
      <div className="mb-1 font-semibold">{title}</div>
      <pre className="max-h-32 overflow-auto whitespace-pre-wrap">{children}</pre>
    </div>
  );
}

export function QueryInspector() {
  const client = useQueryClient();
  const cache = client.getQueryCache().getAll();
  return (
    <Panel title="Query Inspector">
      {JSON.stringify(
        cache.map((q) => ({ key: q.queryKey, state: q.state.status, dataUpdatedAt: q.state.dataUpdatedAt })),
        null,
        2,
      )}
    </Panel>
  );
}

export function WorkflowInspector() {
  return (
    <Panel title="Workflow Inspector">
      {JSON.stringify(runtimeTelemetry.getSpans().filter((s) => s.domain === "workflow"), null, 2)}
    </Panel>
  );
}

export function RealtimeInspector() {
  const [events, setEvents] = React.useState<string>("[]");
  React.useEffect(() => {
    const unsub = eventStreamRuntime.subscribe("notification", () => {
      setEvents(JSON.stringify(eventStreamRuntime.replay("notification").slice(0, 5), null, 2));
    });
    setEvents(JSON.stringify(eventStreamRuntime.replay("notification").slice(0, 5), null, 2));
    return unsub;
  }, []);
  return <Panel title="Realtime Inspector">{events}</Panel>;
}

export function RuntimeTraceViewer() {
  const snapshot = runtimeTelemetry.snapshot();
  return (
    <Panel title="Runtime Trace Viewer">
      {JSON.stringify(
        {
          snapshot,
          metrics: runtimeTelemetry.getMetrics(),
          rollbacks: runtimeTelemetry.getRollbacks().slice(0, 5),
          cacheHits: runtimeTelemetry.getCacheHits().slice(0, 5),
        },
        null,
        2,
      )}
    </Panel>
  );
}

export function RuntimeCorrectnessInspector() {
  return (
    <Panel title="Runtime Correctness">
      {JSON.stringify(
        {
          consensus: consensusCoordination.getState(),
          fencing: consensusCoordination.getFencingToken(),
          transactions: runtimeTransaction.list().slice(-5),
          eventStore: runtimeEventStore.stats(),
          faultTolerance: runtimeFaultTolerance.stats(),
          policies: agentPolicyEngine.listPolicies().map((p) => p.id),
        },
        null,
        2,
      )}
    </Panel>
  );
}

export function DistributedSystemsInspector() {
  return (
    <Panel title="Distributed Systems">
      {JSON.stringify(
        {
          consistency: runtimeConsistency.stats(),
          coordination: distributedCoordination.status(),
          storage: {
            snapshots: runtimeStorage.listSnapshots().length,
            events: runtimeStorage.listEvents().length,
            graphs: runtimeStorage.listGraphs().length,
          },
          security: { audits: runtimeSecurity.getAuditTrail().length },
          governance: agentGovernance.stats(),
        },
        null,
        2,
      )}
    </Panel>
  );
}

export function SystemsEngineeringInspector() {
  return (
    <Panel title="Systems Engineering">
      {JSON.stringify(
        {
          scheduler: runtimeScheduler.stats(),
          distributed: distributedRuntime.sync(),
          persistence: runtimePersistence.listCheckpoints().map((c) => c.id),
        },
        null,
        2,
      )}
    </Panel>
  );
}

export function OrchestrationInspector() {
  return (
    <Panel title="Orchestration Inspector">
      {JSON.stringify(
        {
          lifecycle: runtimeBus.getLifecycle(),
          telemetry: telemetryPipeline.exportSnapshot(),
          workflowGraph: workflowGraph.snapshot("workflow"),
          quoteGraph: quoteGraph.snapshot("quote"),
        },
        null,
        2,
      )}
    </Panel>
  );
}

export function RuntimeDevToolsPanel({ enabled = process.env.NODE_ENV === "development" }: { enabled?: boolean }) {
  const [open, setOpen] = React.useState(false);
  if (!enabled) return null;
  return (
    <div className="fixed bottom-4 right-4 z-[100]">
      <button
        className="rounded-full border bg-white px-3 py-1 text-xs shadow dark:border-zinc-700 dark:bg-zinc-900"
        onClick={() => setOpen((v) => !v)}
      >
        Runtime DevTools
      </button>
      {open ? (
        <div className="mt-2 w-[420px] space-y-2 rounded-lg border bg-white p-3 shadow-lg dark:border-zinc-700 dark:bg-zinc-900">
          <QueryInspector />
          <WorkflowInspector />
          <RealtimeInspector />
          <RuntimeTraceViewer />
          <OrchestrationInspector />
          <SystemsEngineeringInspector />
          <DistributedSystemsInspector />
          <RuntimeCorrectnessInspector />
        </div>
      ) : null}
    </div>
  );
}
