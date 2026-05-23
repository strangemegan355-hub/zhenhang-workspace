export type GraphNode = {
  id: string;
  label: string;
  kind: "workflow" | "quote" | "event" | "runtime";
  meta?: Record<string, unknown>;
};

export type GraphEdge = {
  from: string;
  to: string;
  label?: string;
};

export type RuntimeGraphSnapshot = {
  name: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  at: string;
};

/** Runtime state graph — workflow / quote / event / dependency views. */
export class RuntimeStateGraph {
  private nodes = new Map<string, GraphNode>();
  private edges: GraphEdge[] = [];

  addNode(node: GraphNode) {
    this.nodes.set(node.id, node);
  }

  addEdge(edge: GraphEdge) {
    this.edges.push(edge);
  }

  linkDependency(from: string, to: string, label?: string) {
    this.addEdge({ from, to, label: label ?? "depends" });
  }

  getNode(id: string) {
    return this.nodes.get(id);
  }

  getDependents(nodeId: string): string[] {
    return this.edges.filter((e) => e.to === nodeId).map((e) => e.from);
  }

  getDependencies(nodeId: string): string[] {
    return this.edges.filter((e) => e.from === nodeId).map((e) => e.to);
  }

  snapshot(name: string): RuntimeGraphSnapshot {
    return {
      name,
      nodes: [...this.nodes.values()],
      edges: [...this.edges],
      at: new Date().toISOString(),
    };
  }

  clear() {
    this.nodes.clear();
    this.edges = [];
  }
}

export function createWorkflowGraph(states: string[], transitions: Array<{ from: string; to: string }>) {
  const g = new RuntimeStateGraph();
  states.forEach((s) => g.addNode({ id: s, label: s, kind: "workflow" }));
  transitions.forEach((t) => g.addEdge({ from: t.from, to: t.to, label: "transition" }));
  return g;
}

export function createQuoteGraph(blocks: string[]) {
  const g = new RuntimeStateGraph();
  blocks.forEach((b) => g.addNode({ id: b, label: b, kind: "quote" }));
  return g;
}

export function createEventGraph(events: Array<{ id: string; channel: string }>) {
  const g = new RuntimeStateGraph();
  events.forEach((e) => g.addNode({ id: e.id, label: e.channel, kind: "event" }));
  return g;
}

export const workflowGraph = createWorkflowGraph(
  ["draft", "submitted", "approved"],
  [
    { from: "draft", to: "submitted" },
    { from: "submitted", to: "approved" },
  ],
);

export const quoteGraph = createQuoteGraph(["equipment_bom", "configurator", "cost_profit", "approval_flow"]);

export const runtimeDependencyGraph = new RuntimeStateGraph();
