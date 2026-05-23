import { agentGovernance } from "@zhenhang/agent-governance";
import { agentPolicyEngine } from "@zhenhang/agent-policy-engine";
import { AgentRuntime } from "@zhenhang/agent-runtime";
import type { AICommandContext } from "@zhenhang/ai-runtime";
import { runtimeBus } from "@zhenhang/runtime-bus";
import { RuntimeStateGraph } from "@zhenhang/runtime-graph";
import { runtimeSecurity } from "@zhenhang/runtime-security";
import { runtimeScheduler, type SchedulePriority } from "@zhenhang/runtime-scheduler";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type AgentLifecycle = "idle" | "planning" | "running" | "paused" | "terminated";

export type AgentGovernanceRule = {
  maxConcurrentAgents: number;
  allowedTools: string[];
  requireSandbox: boolean;
};

export type AgentDescriptor = {
  id: string;
  name: string;
  lifecycle: AgentLifecycle;
  permissions: string[];
  sandboxId?: string;
};

/** Agent OS — multi-agent coordination with governance + security layers. */
export class AgentOS {
  private agents = new Map<string, AgentDescriptor>();
  private agentRuntimes = new Map<string, AgentRuntime>();
  private taskGraph = new RuntimeStateGraph();
  private toolGraph = new RuntimeStateGraph();
  private allowedTools: string[] = [];

  setGovernance(rule: Partial<AgentGovernanceRule>) {
    if (rule.maxConcurrentAgents != null) {
      agentGovernance.setQuota({ maxAgents: rule.maxConcurrentAgents });
    }
    if (rule.allowedTools) this.allowedTools = rule.allowedTools;
  }

  spawnAgent(id: string, name: string, ctx: Partial<AICommandContext>): AgentDescriptor {
    if (!agentGovernance.canSpawnAgent()) {
      throw new Error("Agent governance: max concurrent agents reached");
    }
    const secure = runtimeSecurity.createSecureContext({
      userId: ctx.userId,
      roles: [],
      permissions: ctx.permissions ?? [],
    });
    const agent: AgentDescriptor = {
      id,
      name,
      lifecycle: "idle",
      permissions: ctx.permissions ?? [],
      sandboxId: secure.sandboxId,
    };
    const runtime = new AgentRuntime();
    runtime.setContext({ permissions: ctx.permissions ?? [], ...ctx });
    this.agents.set(id, agent);
    this.agentRuntimes.set(id, runtime);
    agentGovernance.onAgentSpawned();
    this.taskGraph.addNode({ id, label: name, kind: "runtime" });
    runtimeBus.dispatch({ type: "agent-os.spawn", domain: "ai", payload: { id, name } });
    return agent;
  }

  registerTool(agentId: string, toolName: string, dependsOn?: string[]) {
    this.toolGraph.addNode({ id: `${agentId}:${toolName}`, label: toolName, kind: "runtime" });
    if (dependsOn) this.toolGraph.linkDependency(dependsOn, `${agentId}:${toolName}`, "tool");
    agentGovernance.registerToolPolicy({
      tool: toolName,
      permissions: ["quote:read"],
      requireApproval: false,
    });
  }

  getAgent(id: string) {
    return this.agents.get(id);
  }

  setLifecycle(id: string, lifecycle: AgentLifecycle) {
    const agent = this.agents.get(id);
    if (!agent) return;
    agent.lifecycle = lifecycle;
    runtimeBus.dispatch({ type: `agent-os.lifecycle.${lifecycle}`, domain: "ai", payload: { id } });
  }

  terminate(id: string) {
    this.setLifecycle(id, "terminated");
    this.agentRuntimes.delete(id);
    this.agents.delete(id);
    agentGovernance.onAgentTerminated();
  }

  async scheduleGoal(agentId: string, goal: string, priority: SchedulePriority = "normal") {
    const runtime = this.agentRuntimes.get(agentId);
    const agent = this.agents.get(agentId);
    if (!runtime || !agent || agent.lifecycle === "terminated") {
      throw new Error(`Agent not available: ${agentId}`);
    }
    if (!agentGovernance.canScheduleGoal()) {
      throw new Error("Agent governance: goal quota exceeded");
    }
    agentGovernance.onGoalScheduled();
    if (!agentGovernance.allocateResources(1, 16)) {
      throw new Error("Agent governance: resource budget exceeded");
    }
    this.setLifecycle(agentId, "planning");
    const policy = await agentPolicyEngine.evaluateWithHooks({
      agentId,
      tool: "agent.goal",
      permissions: agent.permissions,
      payload: { goal },
    });
    if (!policy.allowed) {
      throw new Error(`Agent policy denied: ${policy.reasons.join("; ")}`);
    }
    if (policy.requiresApproval) {
      agentGovernance.requestApproval(agentId, "agent.goal");
    }
    return runtimeScheduler.enqueue({
      id: `agent-${agentId}-${Date.now()}`,
      domain: `agent:${agentId}`,
      priority,
      fn: async () => {
        const secure = runtimeSecurity.createSecureContext({
          userId: agentId,
          permissions: agent.permissions,
        });
        await runtimeSecurity.executeInSandbox(secure, "agent-goals", "execute", async () => {
          this.setLifecycle(agentId, "running");
          const plan = runtime.plan(goal, this.allowedTools.length ? this.allowedTools : undefined);
          for (const step of plan.steps) {
            const stepPolicy = agentPolicyEngine.evaluate({
              agentId,
              tool: step.tool,
              permissions: agent.permissions,
            });
            if (stepPolicy.requiresApproval || agentGovernance.requiresApproval(step.tool)) {
              agentGovernance.requestApproval(agentId, step.tool);
            }
            if (!stepPolicy.allowed) {
              throw new Error(`Policy denied tool: ${step.tool}`);
            }
            if (!agentGovernance.checkToolPermission(secure, step.tool)) {
              throw new Error(`Tool not permitted: ${step.tool}`);
            }
            this.taskGraph.addNode({ id: step.id, label: step.tool, kind: "runtime" });
            step.dependsOn?.forEach((dep) => this.taskGraph.linkDependency(dep, step.id, "task"));
          }
          const result = await runtime.execute(plan);
          this.setLifecycle(agentId, result.success ? "idle" : "paused");
          runtimeTelemetry.increment(result.success ? "agent-os.success" : "agent-os.failure");
        });
        agentGovernance.releaseResources(1, 16);
      },
    });
  }

  taskGraphSnapshot() {
    return this.taskGraph.snapshot("agent-task-graph");
  }

  toolGraphSnapshot() {
    return this.toolGraph.snapshot("agent-tool-graph");
  }
}

export const agentOS = new AgentOS();

export { agentGovernance } from "@zhenhang/agent-governance";
