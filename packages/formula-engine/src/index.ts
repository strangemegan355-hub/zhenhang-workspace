export type FormulaContext = Record<string, number | string | boolean>;

export type FormulaAST = {
  type: "literal" | "ref" | "binary";
  value?: number;
  ref?: string;
  op?: "+" | "-" | "*" | "/";
  left?: FormulaAST;
  right?: FormulaAST;
};

const ALLOWED_OPS = new Set(["+", "-", "*", "/"]);
const REF_PATTERN = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

/** Minimal safe formula parser — no eval(). */
export function parseFormula(expression: string): FormulaAST {
  const trimmed = expression.replace(/\s+/g, "");
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return { type: "literal", value: Number(trimmed) };
  }
  for (const op of ["/", "*", "-", "+"] as const) {
    const idx = trimmed.lastIndexOf(op);
    if (idx > 0) {
      return {
        type: "binary",
        op,
        left: parseFormula(trimmed.slice(0, idx)),
        right: parseFormula(trimmed.slice(idx + 1)),
      };
    }
  }
  if (REF_PATTERN.test(trimmed)) return { type: "ref", ref: trimmed };
  throw new Error(`Invalid formula: ${expression}`);
}

export function buildDependencyGraph(formulas: Record<string, string>): Map<string, string[]> {
  const graph = new Map<string, string[]>();
  for (const [field, expr] of Object.entries(formulas)) {
    const refs = collectRefs(parseFormula(expr));
    graph.set(field, refs);
  }
  return graph;
}

function collectRefs(ast: FormulaAST): string[] {
  if (ast.type === "ref" && ast.ref) return [ast.ref];
  if (ast.type === "binary") {
    return [...collectRefs(ast.left!), ...collectRefs(ast.right!)];
  }
  return [];
}

/** Sandbox execution — only numbers and whitelisted ops. */
export function evaluateAST(ast: FormulaAST, ctx: FormulaContext): number {
  if (ast.type === "literal") return ast.value ?? 0;
  if (ast.type === "ref") {
    const v = ctx[ast.ref!];
    return typeof v === "number" ? v : Number(v) || 0;
  }
  if (ast.type === "binary" && ast.op && ALLOWED_OPS.has(ast.op)) {
    const l = evaluateAST(ast.left!, ctx);
    const r = evaluateAST(ast.right!, ctx);
    switch (ast.op) {
      case "+":
        return l + r;
      case "-":
        return l - r;
      case "*":
        return l * r;
      case "/":
        return r === 0 ? 0 : l / r;
    }
  }
  throw new Error("Unsafe formula evaluation");
}

const computeCache = new Map<string, number>();

export function evaluateFormula(expression: string, ctx: FormulaContext, useCache = true): number {
  const cacheKey = `${expression}::${JSON.stringify(ctx)}`;
  if (useCache && computeCache.has(cacheKey)) return computeCache.get(cacheKey)!;
  const ast = parseFormula(expression);
  const result = evaluateAST(ast, ctx);
  if (useCache) {
    computeCache.set(cacheKey, result);
    if (computeCache.size > 1000) computeCache.clear();
  }
  return result;
}

/** Dynamic pricing via formula set. */
export function evaluatePricingFormulas(
  formulas: Record<string, string>,
  ctx: FormulaContext,
): Record<string, number> {
  const graph = buildDependencyGraph(formulas);
  const out: Record<string, number> = { ...Object.fromEntries(Object.entries(ctx).filter(([, v]) => typeof v === "number")) };
  const order = topologicalSort(graph);
  for (const field of order) {
    out[field] = evaluateFormula(formulas[field], out as FormulaContext, true);
  }
  return out;
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

export function clearFormulaCache() {
  computeCache.clear();
}
