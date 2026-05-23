import { runtimeSecurity, type SecureRuntimeContext } from "@zhenhang/runtime-security";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type AgentQuota = {
  maxAgents: number;
  maxGoalsPerHour: number;
  maxToolCallsPerGoal: number;
};

export type ResourceBudget = {
  cpuUnits: number;
  memoryMb: number;
  usedCpu: number;
  usedMemory: number;
};

export type ToolPermissionPolicy = {
  tool: string;
  permissions: string[];
  requireApproval: boolean;
};

export type ApprovalRequest = {
  id: string;
  agentId: string;
  tool: string;
  status: "pending" | "approved" | "rejected";
  at: string;
};

export type ExecutionBoundary = {
  allowNetwork: boolean;
  allowFileWrite: boolean;
  maxExecutionMs: number;
};

/** Agent governance — quota, budget, tool policy, human approval, boundaries. */
export class AgentGovernanceLayer {
  private quota: AgentQuota = { maxAgents: 4, maxGoalsPerHour: 20, maxToolCallsPerGoal: 10 };
  private budget: ResourceBudget = { cpuUnits: 100, memoryMb: 512, usedCpu: 0, usedMemory: 0 };
  private toolPolicies: ToolPermissionPolicy[] = [];
  private approvals: ApprovalRequest[] = [];
  private boundaries: ExecutionBoundary = {
    allowNetwork: false,
    allowFileWrite: false,
    maxExecutionMs: 30_000,
  };
  private agentCount = 0;
  private goalsThisHour = 0;
  private hourStarted = Date.now();

  setQuota(quota: Partial<AgentQuota>) {
    this.quota = { ...this.quota, ...quota };
  }

  setBudget(budget: Partial<ResourceBudget>) {
    this.budget = { ...this.budget, ...budget };
  }

  setBoundaries(boundaries: Partial<ExecutionBoundary>) {
    this.boundaries = { ...this.boundaries, ...boundaries };
  }

  registerToolPolicy(policy: ToolPermissionPolicy) {
    this.toolPolicies.push(policy);
    runtimeSecurity.grantToolAccess(policy.tool, "agent-tools", policy.permissions.length > 0);
  }

  canSpawnAgent(): boolean {
    return this.agentCount < this.quota.maxAgents;
  }

  onAgentSpawned() {
    this.agentCount += 1;
  }

  onAgentTerminated() {
    this.agentCount = Math.max(0, this.agentCount - 1);
  }

  canScheduleGoal(): boolean {
    const hourMs = 60 * 60 * 1000;
    if (Date.now() - this.hourStarted > hourMs) {
      this.goalsThisHour = 0;
      this.hourStarted = Date.now();
    }
    return this.goalsThisHour < this.quota.maxGoalsPerHour;
  }

  onGoalScheduled() {
    this.goalsThisHour += 1;
  }

  allocateResources(cpu: number, memoryMb: number): boolean {
    if (this.budget.usedCpu + cpu > this.budget.cpuUnits) return false;
    if (this.budget.usedMemory + memoryMb > this.budget.memoryMb) return false;
    this.budget.usedCpu += cpu;
    this.budget.usedMemory += memoryMb;
    return true;
  }

  releaseResources(cpu: number, memoryMb: number) {
    this.budget.usedCpu = Math.max(0, this.budget.usedCpu - cpu);
    this.budget.usedMemory = Math.max(0, this.budget.usedMemory - memoryMb);
  }

  checkToolPermission(ctx: SecureRuntimeContext, tool: string): boolean {
    const policy = this.toolPolicies.find((p) => p.tool === tool);
    if (!policy) return runtimeSecurity.canAccessTool(ctx, tool, "agent-tools");
    return policy.permissions.every((p) => ctx.permissions.includes(p) || ctx.permissions.includes("*:*:*"));
  }

  requestApproval(agentId: string, tool: string): ApprovalRequest {
    const req: ApprovalRequest = {
      id: `apr-${Date.now()}`,
      agentId,
      tool,
      status: "pending",
      at: new Date().toISOString(),
    };
    this.approvals.unshift(req);
    runtimeTelemetry.log("info", "agent.governance.approval.requested", req);
    return req;
  }

  resolveApproval(id: string, approved: boolean) {
    const req = this.approvals.find((a) => a.id === id);
    if (!req) return null;
    req.status = approved ? "approved" : "rejected";
    return req;
  }

  requiresApproval(tool: string): boolean {
    return this.toolPolicies.find((p) => p.tool === tool)?.requireApproval ?? false;
  }

  getExecutionBoundary(): ExecutionBoundary {
    return { ...this.boundaries };
  }

  stats() {
    return {
      quota: this.quota,
      agentCount: this.agentCount,
      goalsThisHour: this.goalsThisHour,
      budget: this.budget,
      pendingApprovals: this.approvals.filter((a) => a.status === "pending").length,
    };
  }
}

export const agentGovernance = new AgentGovernanceLayer();
