import {
  buildDependencyGraph,
  evaluateFormula,
  parseFormula,
  type FormulaContext,
} from "@zhenhang/formula-engine";
import { runtimeBus } from "@zhenhang/runtime-bus";
import { RuntimeStateGraph } from "@zhenhang/runtime-graph";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type FormulaNodeState = {
  field: string;
  expression: string;
  value?: number;
  dirty: boolean;
};

/** Formula runtime graph — invalidation, cache, recompute orchestration. */
export class FormulaRuntimeGraph {
  private formulas: Record<string, string> = {};
  private depGraph = new Map<string, string[]>();
  private reverseDep = new Map<string, Set<string>>();
  private nodes = new Map<string, FormulaNodeState>();
  private values: Record<string, number> = {};
  private stateGraph = new RuntimeStateGraph();

  loadFormulas(formulas: Record<string, string>) {
    this.formulas = { ...formulas };
    this.depGraph = buildDependencyGraph(formulas);
    this.reverseDep.clear();
    for (const [field, deps] of this.depGraph) {
      this.nodes.set(field, { field, expression: formulas[field], dirty: true });
      this.stateGraph.addNode({ id: field, label: field, kind: "runtime" });
      deps.forEach((dep) => {
        this.stateGraph.linkDependency(dep, field, "formula");
        if (!this.reverseDep.has(dep)) this.reverseDep.set(dep, new Set());
        this.reverseDep.get(dep)!.add(field);
      });
    }
  }

  setInput(key: string, value: number) {
    this.values[key] = value;
    this.invalidate(key);
  }

  invalidate(field: string) {
    const queue = [field];
    const visited = new Set<string>();
    while (queue.length) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);
      const node = this.nodes.get(current);
      if (node) node.dirty = true;
      const dependents = this.reverseDep.get(current);
      dependents?.forEach((d) => queue.push(d));
    }
    runtimeBus.dispatch({ type: "formula.invalidate", domain: "formula", payload: { field, visited: [...visited] } });
  }

  recompute(fields?: string[]): Record<string, number> {
    const span = runtimeTelemetry.startSpan("formula.recompute", "formula");
    const order = fields ?? topologicalOrder(this.depGraph);
    for (const field of order) {
      const node = this.nodes.get(field);
      if (!node || !node.dirty) continue;
      const expr = this.formulas[field];
      if (!expr) continue;
      try {
        parseFormula(expr);
        this.values[field] = evaluateFormula(expr, this.values as FormulaContext, true);
        node.dirty = false;
        node.value = this.values[field];
      } catch (err) {
        runtimeTelemetry.log("error", `formula.recompute:${field}`, err);
      }
    }
    runtimeTelemetry.endSpan(span);
    runtimeBus.dispatch({ type: "formula.recomputed", domain: "formula", payload: { values: { ...this.values } } });
    return { ...this.values };
  }

  getValues() {
    return { ...this.values };
  }

  snapshot() {
    return this.stateGraph.snapshot("formula-runtime");
  }
}

function topologicalOrder(graph: Map<string, string[]>): string[] {
  const visited = new Set<string>();
  const result: string[] = [];
  const visit = (node: string) => {
    if (visited.has(node)) return;
    visited.add(node);
    for (const dep of graph.get(node) ?? []) visit(dep);
    result.push(node);
  };
  for (const node of graph.keys()) visit(node);
  return result;
}

export const formulaRuntimeGraph = new FormulaRuntimeGraph();

export { formulaDAGEngine, FormulaDAGEngine } from "@zhenhang/formula-dag";
