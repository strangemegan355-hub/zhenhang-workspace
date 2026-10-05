import {
  buildDependencyGraph,
  evaluateFormula,
  parseFormula,
  type FormulaAST,
  type FormulaContext,
} from "@zhenhang/formula-engine";
import { runtimeBus } from "@zhenhang/runtime-bus";

export type CompiledFormula = {
  field: string;
  expression: string;
  ast: FormulaAST;
  dependencies: string[];
};

export type TopologyCache = {
  order: string[];
  compiled: Map<string, CompiledFormula>;
  at: string;
};

/** Formula DAG engine — compile, cycle detect, topology cache, incremental recompute. */
export class FormulaDAGEngine {
  private topology: TopologyCache | null = null;
  private values: Record<string, number> = {};
  private dirty = new Set<string>();

  compile(formulas: Record<string, string>): TopologyCache {
    const depGraph = buildDependencyGraph(formulas);
    const cycles = detectCycles(depGraph);
    if (cycles.length > 0) {
      throw new Error(`Formula cycle detected: ${cycles.join(" -> ")}`);
    }
    const compiled = new Map<string, CompiledFormula>();
    for (const [field, expr] of Object.entries(formulas)) {
      const ast = parseFormula(expr);
      compiled.set(field, {
        field,
        expression: expr,
        ast,
        dependencies: depGraph.get(field) ?? [],
      });
    }
    const order = topologicalSort(depGraph);
    this.topology = { order, compiled, at: new Date().toISOString() };
    runtimeBus.dispatch({ type: "formula-dag.compiled", domain: "formula", payload: { fields: order.length } });
    return this.topology;
  }

  getTopology(): TopologyCache | null {
    return this.topology;
  }

  setInput(key: string, value: number) {
    this.values[key] = value;
    this.markDirty(key);
  }

  private markDirty(field: string) {
    if (!this.topology) return;
    const queue = [field];
    while (queue.length) {
      const current = queue.shift()!;
      this.dirty.add(current);
      for (const [f, compiled] of this.topology.compiled) {
        if (compiled.dependencies.includes(current)) queue.push(f);
      }
    }
  }

  /** Incremental recompute — only dirty nodes in topological order. */
  recomputeIncremental(): Record<string, number> {
    if (!this.topology) return { ...this.values };
    for (const field of this.topology.order) {
      if (!this.dirty.has(field)) continue;
      const compiled = this.topology.compiled.get(field);
      if (!compiled) continue;
      this.values[field] = evaluateFormula(compiled.expression, this.values as FormulaContext, true);
      this.dirty.delete(field);
    }
    runtimeBus.dispatch({ type: "formula-dag.recomputed", domain: "formula", payload: { ...this.values } });
    return { ...this.values };
  }

  recomputeFull(): Record<string, number> {
    if (!this.topology) return { ...this.values };
    this.topology.order.forEach((f) => this.dirty.add(f));
    return this.recomputeIncremental();
  }
}

function detectCycles(graph: Map<string, string[]>): string[] {
  const visited = new Set<string>();
  const stack = new Set<string>();
  const path: string[] = [];
  let cycle: string[] = [];

  const dfs = (node: string): boolean => {
    if (stack.has(node)) {
      cycle = [...path, node];
      return true;
    }
    if (visited.has(node)) return false;
    visited.add(node);
    stack.add(node);
    path.push(node);
    for (const dep of graph.get(node) ?? []) {
      if (dfs(dep)) return true;
    }
    path.pop();
    stack.delete(node);
    return false;
  };

  for (const node of graph.keys()) {
    if (dfs(node)) return cycle;
  }
  return [];
}

function topologicalSort(graph: Map<string, string[]>): string[] {
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

export const formulaDAGEngine = new FormulaDAGEngine();
