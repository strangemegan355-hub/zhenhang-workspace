import {
  AICommandBus,
  defaultAICommandBus,
  type AICommandAuditRecord,
  type AICommandContext,
  type AICommandDefinition,
} from "@zhenhang/ai-command";
import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type AIToolDefinition = {
  name: string;
  description: string;
  parameters?: Record<string, unknown>;
  commandName: string;
};

export type MemoryEntry = {
  key: string;
  value: unknown;
  updatedAt: string;
};

/** AI Runtime — tool registry + context/memory + sandboxed command execution. */
export class AIRuntime {
  private bus: AICommandBus;
  private tools = new Map<string, AIToolDefinition>();
  private context: AICommandContext = { permissions: [] };
  private memory = new Map<string, MemoryEntry>();
  private auditRecords: AICommandAuditRecord[] = [];

  constructor(bus: AICommandBus = defaultAICommandBus) {
    this.bus = new AICommandBus((record) => {
      this.auditRecords.unshift(record);
      if (this.auditRecords.length > 100) this.auditRecords.pop();
      runtimeTelemetry.log("info", `ai.audit:${record.command}`, record);
    });
    defaultAICommandBus.listSafeCommands().forEach((cmd) => {
      this.registerTool({
        name: cmd.name,
        description: cmd.description ?? cmd.name,
        commandName: cmd.name,
      });
    });
  }

  registerTool(tool: AIToolDefinition) {
    this.tools.set(tool.name, tool);
  }

  registerCommand<TPayload, TResult>(def: AICommandDefinition<TPayload, TResult>) {
    this.bus.register(def);
    this.registerTool({
      name: def.name,
      description: def.description ?? def.name,
      commandName: def.name,
    });
  }

  setContext(ctx: Partial<AICommandContext>) {
    this.context = { ...this.context, ...ctx };
  }

  injectContext(extra: Record<string, unknown>): AICommandContext {
    this.context = this.bus.injectContext(this.context, extra);
    return this.context;
  }

  setMemory(key: string, value: unknown) {
    this.memory.set(key, { key, value, updatedAt: new Date().toISOString() });
  }

  getMemory(key: string): unknown {
    return this.memory.get(key)?.value;
  }

  listTools(): AIToolDefinition[] {
    return [...this.tools.values()];
  }

  getAuditTrail(): AICommandAuditRecord[] {
    return [...this.auditRecords];
  }

  /** Sandbox — only AI-safe commands via command bus. */
  async executeTool<TPayload, TResult>(toolName: string, payload: TPayload): Promise<TResult> {
    const tool = this.tools.get(toolName);
    if (!tool) throw new Error(`Unknown AI tool: ${toolName}`);
    const span = runtimeTelemetry.startSpan(`ai.tool.${toolName}`, "ai");
    try {
      const result = await this.bus.execute<TPayload, TResult>(tool.commandName, payload, this.context);
      runtimeTelemetry.increment("ai.tool.success");
      return result;
    } catch (err) {
      runtimeTelemetry.increment("ai.tool.error");
      throw err;
    } finally {
      runtimeTelemetry.endSpan(span);
    }
  }
}

export const aiRuntime = new AIRuntime();

export { AICommandBus, type AICommandContext, type AICommandAuditRecord } from "@zhenhang/ai-command";
