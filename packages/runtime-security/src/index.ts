import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type RuntimeACLRule = {
  resource: string;
  actions: string[];
  roles?: string[];
  permissions?: string[];
};

export type ExecutionAuditRecord = {
  id: string;
  actor?: string;
  action: string;
  resource: string;
  allowed: boolean;
  at: string;
  meta?: Record<string, unknown>;
};

export type SecureRuntimeContext = {
  userId?: string;
  roles: string[];
  permissions: string[];
  sandboxId: string;
  dataScope?: string;
};

export type ToolAccessEdge = { tool: string; resource: string; allowed: boolean };

/** Runtime security — ACL, sandbox, audit, tool access graph. */
export class RuntimeSecurityLayer {
  private acl: RuntimeACLRule[] = [];
  private audits: ExecutionAuditRecord[] = [];
  private toolAccessGraph: ToolAccessEdge[] = [];
  private sandboxes = new Set<string>();

  defineACL(rule: RuntimeACLRule) {
    this.acl.push(rule);
  }

  createSandbox(sandboxId: string) {
    this.sandboxes.add(sandboxId);
    return sandboxId;
  }

  isSandboxActive(sandboxId: string) {
    return this.sandboxes.has(sandboxId);
  }

  createSecureContext(ctx: Omit<SecureRuntimeContext, "sandboxId"> & { sandboxId?: string }): SecureRuntimeContext {
    const sandboxId = ctx.sandboxId ?? this.createSandbox(`sandbox-${Date.now()}`);
    return { ...ctx, sandboxId };
  }

  checkACL(ctx: SecureRuntimeContext, resource: string, action: string): boolean {
    const rules = this.acl.filter((r) => r.resource === resource || r.resource === "*");
    if (rules.length === 0) return ctx.permissions.includes("*:*:*");
    return rules.some((rule) => {
      if (!rule.actions.includes(action) && !rule.actions.includes("*")) return false;
      if (rule.permissions?.length) {
        return rule.permissions.some((p) => ctx.permissions.includes(p));
      }
      return true;
    });
  }

  grantToolAccess(tool: string, resource: string, allowed: boolean) {
    this.toolAccessGraph.push({ tool, resource, allowed });
  }

  canAccessTool(ctx: SecureRuntimeContext, tool: string, resource: string): boolean {
    const edge = this.toolAccessGraph.find((e) => e.tool === tool && e.resource === resource);
    if (edge) return edge.allowed;
    return this.checkACL(ctx, resource, "execute");
  }

  audit(record: Omit<ExecutionAuditRecord, "id" | "at">) {
    const full: ExecutionAuditRecord = {
      ...record,
      id: `audit-${Date.now()}`,
      at: new Date().toISOString(),
    };
    this.audits.unshift(full);
    if (this.audits.length > 200) this.audits.pop();
    runtimeTelemetry.log(full.allowed ? "info" : "warn", `security.audit:${record.action}`, full);
    return full;
  }

  /** Sandbox-isolated execution wrapper. */
  async executeInSandbox<T>(
    ctx: SecureRuntimeContext,
    resource: string,
    action: string,
    fn: () => Promise<T>,
  ): Promise<T> {
    if (!this.isSandboxActive(ctx.sandboxId)) {
      throw new Error("Sandbox not active");
    }
    const allowed = this.checkACL(ctx, resource, action);
    this.audit({ actor: ctx.userId, action, resource, allowed, meta: { sandboxId: ctx.sandboxId } });
    if (!allowed) throw new Error(`ACL denied: ${action} on ${resource}`);
    return fn();
  }

  getAuditTrail() {
    return [...this.audits];
  }

  getToolAccessGraph() {
    return [...this.toolAccessGraph];
  }
}

export const runtimeSecurity = new RuntimeSecurityLayer();
