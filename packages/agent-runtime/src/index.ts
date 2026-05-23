import { aiRuntime, type AICommandContext } from "@zhenhang/ai-runtime";
import { runtimeBus } from "@zhenhang/runtime-bus";
import { RuntimeStateGraph } from "@zhenhang/runtime-graph";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type AgentPlanStep = {
  id: string;
  tool: string;
  payload?: Record<string, unknown>;
  dependsOn?: string[];
};

export type AgentPlan = {
  goal: string;
  steps: AgentPlanStep[];
};

export type AgentExecutionResult = {
  planId: string;
  outputs: Record<string, unknown>;
  success: boolean;
};

/** AI Agent runtime — planner, executor, scheduler, memory/context graphs. */
export class AgentRuntime {
  private memoryGraph = new RuntimeStateGraph();
  private contextGraph = new RuntimeStateGraph();
  private queue: AgentPlanStep[] = [];
  private running = false;

  constructor(private ai = aiRuntime) {}

  setContext(ctx: Partial<AICommandContext>) {
    this.ai.setContext(ctx);
    Object.entries(ctx).forEach(([k, v]) => {
      this.contextGraph.addNode({ id: k, label: String(k), kind: "runtime", meta: { value: v } });
    });
  }

  injectContext(extra: Record<string, unknown>) {
    return this.ai.injectContext(extra);
  }

  setMemory(key: string, value: unknown) {
    this.ai.setMemory(key, value);
    this.memoryGraph.addNode({ id: key, label: key, kind: "runtime", meta: { value } });
  }

  getMemory(key: string) {
    return this.ai.getMemory(key);
  }

  /** Planner — build tool execution plan from goal. */
  plan(goal: string, tools?: string[]): AgentPlan {
    const available = tools ?? this.ai.listTools().map((t) => t.name);
    const steps: AgentPlanStep[] = available.slice(0, 3).map((tool, idx) => ({
      id: `step-${idx + 1}`,
      tool,
      payload: { goal },
      dependsOn: idx > 0 ? [`step-${idx}`] : undefined,
    }));
    const plan: AgentPlan = { goal, steps };
    runtimeBus.dispatch({ type: "agent.plan", domain: "ai", payload: plan });
    return plan;
  }

  /** Tool scheduler — topological schedule of plan steps. */
  schedule(plan: AgentPlan): AgentPlanStep[] {
    const ordered: AgentPlanStep[] = [];
    const done = new Set<string>();
    const steps = [...plan.steps];
    while (ordered.length < steps.length) {
      const next = steps.find((s) => !done.has(s.id) && (s.dependsOn ?? []).every((d) => done.has(d)));
      if (!next) break;
      ordered.push(next);
      done.add(next.id);
    }
    this.queue = ordered;
    return ordered;
  }

  /** Executor — run scheduled steps in sandbox via ai-runtime. */
  async execute(plan: AgentPlan): Promise<AgentExecutionResult> {
    if (this.running) throw new Error("Agent runtime busy");
    this.running = true;
    const planId = `plan-${Date.now()}`;
    const outputs: Record<string, unknown> = {};
    const span = runtimeTelemetry.startSpan("agent.execute", "ai");
    try {
      const steps = this.schedule(plan);
      for (const step of steps) {
        await runtimeBus.coordinate(`agent.step.${step.id}`, ["ai"], async () => {
          const out = await this.ai.executeTool(step.tool, step.payload ?? {});
          outputs[step.id] = out;
          this.setMemory(step.id, out);
        });
      }
      return { planId, outputs, success: true };
    } catch {
      runtimeBus.dispatch({ type: "agent.execute.error", domain: "ai", payload: { planId } });
      return { planId, outputs, success: false };
    } finally {
      this.running = false;
      runtimeTelemetry.endSpan(span);
    }
  }

  memorySnapshot() {
    return this.memoryGraph.snapshot("agent-memory");
  }

  contextSnapshot() {
    return this.contextGraph.snapshot("agent-context");
  }
}

export const agentRuntime = new AgentRuntime();
