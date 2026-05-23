export type AICommandContext = {
  userId?: string;
  sessionId?: string;
  bizType?: string;
  bizId?: string;
  permissions: string[];
  dataScope?: string;
  extra?: Record<string, unknown>;
};

export type AICommandAuditRecord = {
  command: string;
  actor?: string;
  bizType?: string;
  bizId?: string;
  payload?: Record<string, unknown>;
  result: "success" | "denied" | "error";
  message?: string;
  at: string;
};

export type AICommandHandler<TPayload = unknown, TResult = unknown> = (
  payload: TPayload,
  ctx: AICommandContext,
) => Promise<TResult> | TResult;

export type AICommandDefinition<TPayload = unknown, TResult = unknown> = {
  name: string;
  description?: string;
  /** Permissions required to execute — empty means ai-safe public read actions only. */
  requiredPermissions: string[];
  safeForAI: boolean;
  handler: AICommandHandler<TPayload, TResult>;
};

type AuditSink = (record: AICommandAuditRecord) => void;

/** Command bus — registers AI-safe actions with permission + audit gates. */
export class AICommandBus {
  private commands = new Map<string, AICommandDefinition>();
  private auditSink: AuditSink;

  constructor(auditSink?: AuditSink) {
    this.auditSink =
      auditSink ??
      ((record) => {
        if (typeof console !== "undefined") {
          console.info("[ai-command:audit]", record);
        }
      });
  }

  register<TPayload, TResult>(def: AICommandDefinition<TPayload, TResult>) {
    this.commands.set(def.name, def as AICommandDefinition);
  }

  listSafeCommands(): Array<Pick<AICommandDefinition, "name" | "description" | "safeForAI">> {
    return [...this.commands.values()]
      .filter((c) => c.safeForAI)
      .map((c) => ({ name: c.name, description: c.description, safeForAI: c.safeForAI }));
  }

  injectContext(base: AICommandContext, extra: Record<string, unknown>): AICommandContext {
    return { ...base, extra: { ...base.extra, ...extra } };
  }

  private permissionAllows(ctx: AICommandContext, required: string[]): boolean {
    if (required.length === 0) return true;
    if (ctx.permissions.includes("*:*:*")) return true;
    return required.every((p) => ctx.permissions.includes(p));
  }

  async execute<TPayload, TResult>(
    name: string,
    payload: TPayload,
    ctx: AICommandContext,
  ): Promise<TResult> {
    const def = this.commands.get(name);
    const at = new Date().toISOString();
    if (!def) {
      this.auditSink({
        command: name,
        actor: ctx.userId,
        bizType: ctx.bizType,
        bizId: ctx.bizId,
        payload: payload as Record<string, unknown>,
        result: "error",
        message: "Unknown command",
        at,
      });
      throw new Error(`Unknown AI command: ${name}`);
    }
    if (!def.safeForAI) {
      this.auditSink({
        command: name,
        actor: ctx.userId,
        result: "denied",
        message: "Command not marked safe for AI",
        at,
      });
      throw new Error(`Command not AI-safe: ${name}`);
    }
    if (!this.permissionAllows(ctx, def.requiredPermissions)) {
      this.auditSink({
        command: name,
        actor: ctx.userId,
        result: "denied",
        message: "Permission denied",
        at,
      });
      throw new Error(`Permission denied for command: ${name}`);
    }
    try {
      const result = await def.handler(payload, ctx);
      this.auditSink({
        command: name,
        actor: ctx.userId,
        bizType: ctx.bizType,
        bizId: ctx.bizId,
        payload: payload as Record<string, unknown>,
        result: "success",
        at,
      });
      return result as TResult;
    } catch (err) {
      this.auditSink({
        command: name,
        actor: ctx.userId,
        result: "error",
        message: err instanceof Error ? err.message : "Execution failed",
        at,
      });
      throw err;
    }
  }
}

export const defaultAICommandBus = new AICommandBus();

defaultAICommandBus.register({
  name: "quote.summarize_diff",
  description: "Summarize quote version diff for assistant context",
  requiredPermissions: ["quote:read"],
  safeForAI: true,
  handler: async (payload: { summary: string }) => payload.summary,
});

defaultAICommandBus.register({
  name: "notification.list_unread",
  description: "List unread notifications metadata",
  requiredPermissions: ["platform:notification:read"],
  safeForAI: true,
  handler: async () => ({ unread: true }),
});
