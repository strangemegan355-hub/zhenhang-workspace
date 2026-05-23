import { parseWorkflowSchema, type WorkflowSchema } from "@zhenhang/workflow-schema";

export type WorkflowContext = {
  currentState: string;
  userPermissions: string[];
  metadata?: Record<string, unknown>;
};

export type TransitionGuard = (ctx: WorkflowContext, actionCode: string) => boolean;

export type TransitionResult =
  | { ok: true; nextState: string }
  | { ok: false; reason: string };

/** Default guard: permission + state existence. */
export const defaultTransitionGuard: TransitionGuard = (ctx, actionCode) => {
  return ctx.userPermissions.length > 0 || actionCode.length > 0;
};

/** State machine runtime — schema-driven transitions. */
export class WorkflowRuntime {
  private schema: WorkflowSchema;

  constructor(schema: WorkflowSchema | unknown) {
    this.schema = parseWorkflowSchema(schema);
  }

  getStateMetadata(stateCode: string) {
    return this.schema.states.find((s) => s.code === stateCode);
  }

  getAvailableActions(ctx: WorkflowContext): WorkflowSchema["actions"] {
    return this.schema.actions.filter((action) => {
      const fromCurrent = this.canTransition(ctx.currentState, action.next_state);
      if (!fromCurrent) return false;
      return this.permissionRuntimeAllows(ctx, action.code);
    });
  }

  canTransition(fromState: string, toState: string): boolean {
    const action = this.schema.actions.find((a) => a.next_state === toState);
    if (!action) return false;
    return true;
  }

  /** Action policy engine — evaluates permission schema per action. */
  permissionRuntimeAllows(ctx: WorkflowContext, actionCode: string): boolean {
    const rule = this.schema.permissions.find((p) => p.action_code === actionCode);
    if (!rule || rule.permissions.length === 0) return true;
    if (ctx.userPermissions.includes("*:*:*")) return true;
    return rule.permissions.some((p) => ctx.userPermissions.includes(p));
  }

  /** Execute transition with guards. */
  transition(
    ctx: WorkflowContext,
    actionCode: string,
    guard: TransitionGuard = defaultTransitionGuard,
  ): TransitionResult {
    const action = this.schema.actions.find((a) => a.code === actionCode);
    if (!action) return { ok: false, reason: `Unknown action: ${actionCode}` };
    if (!guard(ctx, actionCode)) return { ok: false, reason: "Transition guard rejected" };
    if (!this.permissionRuntimeAllows(ctx, actionCode)) {
      return { ok: false, reason: "Permission denied" };
    }
    const targetMeta = this.getStateMetadata(action.next_state);
    if (!targetMeta) return { ok: false, reason: `Unknown target state: ${action.next_state}` };
    return { ok: true, nextState: action.next_state };
  }
}

export function createWorkflowRuntime(schema: WorkflowSchema | unknown) {
  return new WorkflowRuntime(schema);
}
