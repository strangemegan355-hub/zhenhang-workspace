import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type PolicyRule = {
  id: string;
  name: string;
  minRisk?: number;
  maxRisk?: number;
  requiredPermissions?: string[];
  requireApproval?: boolean;
  escalateTo?: string;
};

export type ExecutionConstraints = {
  maxDurationMs: number;
  maxToolCalls: number;
  allowedDomains: string[];
};

export type PolicyEvaluation = {
  allowed: boolean;
  riskScore: number;
  requiresApproval: boolean;
  escalation?: string;
  reasons: string[];
};

export type GovernanceHook = {
  beforeExecute?: (ctx: PolicyContext) => PolicyEvaluation | Promise<PolicyEvaluation>;
  afterExecute?: (ctx: PolicyContext, result: unknown) => void;
};

export type PolicyContext = {
  agentId: string;
  tool: string;
  permissions: string[];
  payload?: Record<string, unknown>;
};

/** Agent policy engine — risk, constraints, approval escalation, registry, hooks. */
export class AgentPolicyEngine {
  private registry = new Map<string, PolicyRule>();
  private hooks: GovernanceHook[] = [];
  private defaultConstraints: ExecutionConstraints = {
    maxDurationMs: 30_000,
    maxToolCalls: 10,
    allowedDomains: ["ai", "quote", "workflow"],
  };

  register(rule: PolicyRule) {
    this.registry.set(rule.id, rule);
  }

  addHook(hook: GovernanceHook) {
    this.hooks.push(hook);
  }

  setConstraints(constraints: Partial<ExecutionConstraints>) {
    this.defaultConstraints = { ...this.defaultConstraints, ...constraints };
  }

  scoreRisk(ctx: PolicyContext): number {
    let score = 0;
    if (!ctx.permissions.length) score += 40;
    if (ctx.tool.includes("delete") || ctx.tool.includes("export")) score += 30;
    if (ctx.tool.includes("approve")) score += 20;
    const rule = [...this.registry.values()].find((r) => r.name === ctx.tool);
    if (rule?.requireApproval) score += 25;
    return Math.min(100, score);
  }

  evaluate(ctx: PolicyContext): PolicyEvaluation {
    const riskScore = this.scoreRisk(ctx);
    const reasons: string[] = [];
    let requiresApproval = riskScore >= 50;
    let escalation: string | undefined;
    let allowed = true;

    for (const rule of this.registry.values()) {
      if (rule.minRisk != null && riskScore < rule.minRisk) continue;
      if (rule.maxRisk != null && riskScore > rule.maxRisk) continue;
      if (rule.requiredPermissions?.length) {
        const missing = rule.requiredPermissions.filter((p) => !ctx.permissions.includes(p));
        if (missing.length) {
          allowed = false;
          reasons.push(`Missing permissions: ${missing.join(",")}`);
        }
      }
      if (rule.requireApproval) {
        requiresApproval = true;
        escalation = rule.escalateTo;
      }
    }

    if (!this.defaultConstraints.allowedDomains.some((d) => ctx.tool.startsWith(d))) {
      reasons.push("Tool outside allowed domains");
    }

    return { allowed, riskScore, requiresApproval, escalation, reasons };
  }

  async evaluateWithHooks(ctx: PolicyContext): Promise<PolicyEvaluation> {
    for (const hook of this.hooks) {
      if (hook.beforeExecute) {
        const result = await hook.beforeExecute(ctx);
        runtimeTelemetry.log("info", "policy.hook.before", { tool: ctx.tool, allowed: result.allowed });
        return result;
      }
    }
    return this.evaluate(ctx);
  }

  notifyAfter(ctx: PolicyContext, result: unknown) {
    this.hooks.forEach((h) => h.afterExecute?.(ctx, result));
  }

  getConstraints(): ExecutionConstraints {
    return { ...this.defaultConstraints };
  }

  listPolicies(): PolicyRule[] {
    return [...this.registry.values()];
  }
}

export const agentPolicyEngine = new AgentPolicyEngine();

agentPolicyEngine.register({
  id: "quote-read",
  name: "quote.summarize_diff",
  maxRisk: 40,
  requiredPermissions: ["quote:read"],
});

agentPolicyEngine.register({
  id: "quote-export",
  name: "quote.export",
  minRisk: 60,
  requireApproval: true,
  escalateTo: "manager",
});
