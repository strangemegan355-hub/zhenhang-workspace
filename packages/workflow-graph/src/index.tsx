import * as React from "react";

export type WorkflowNode = { id: string; label: string };
export type WorkflowEdge = { from: string; to: string };

export function WorkflowGraph({
  nodes,
  edges,
  currentNodeId,
}: {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  currentNodeId?: string;
}) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        {nodes.map((n) => (
          <div
            key={n.id}
            className={`rounded-md border px-3 py-2 text-sm ${n.id === currentNodeId ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30" : ""}`}
          >
            {n.label}
          </div>
        ))}
      </div>
      <div className="text-xs text-zinc-500">{edges.map((e) => `${e.from} -> ${e.to}`).join(" | ")}</div>
    </div>
  );
}
