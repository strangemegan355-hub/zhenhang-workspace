
export type RuntimeLifecyclePhase = "boot" | "ready" | "pause" | "resume" | "shutdown";

export type RuntimeEvent<T = unknown> = {
  type: string;
  domain: string;
  payload?: T;
  at: string;
};

export type RuntimeMiddleware = (
  event: RuntimeEvent,
  next: () => void | Promise<void>,
) => void | Promise<void>;

export type RuntimeHook = {
  onLifecycle?: (phase: RuntimeLifecyclePhase) => void;
  onEvent?: (event: RuntimeEvent) => void;
};

/** Unified runtime bus — event dispatch, lifecycle, hooks, middleware. */
export class RuntimeBus {
  private phase: RuntimeLifecyclePhase = "boot";
  private middlewares: RuntimeMiddleware[] = [];
  private hooks = new Set<RuntimeHook>();
  private listeners = new Map<string, Set<(event: RuntimeEvent) => void>>();

  use(middleware: RuntimeMiddleware) {
    this.middlewares.push(middleware);
    return () => {
      const idx = this.middlewares.indexOf(middleware);
      if (idx >= 0) this.middlewares.splice(idx, 1);
    };
  }

  registerHook(hook: RuntimeHook) {
    this.hooks.add(hook);
    return () => this.hooks.delete(hook);
  }

  on(type: string, handler: (event: RuntimeEvent) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(handler);
    return () => this.listeners.get(type)?.delete(handler);
  }

  setLifecycle(phase: RuntimeLifecyclePhase) {
    this.phase = phase;
    this.hooks.forEach((h) => h.onLifecycle?.(phase));
    this.dispatch({ type: `lifecycle.${phase}`, domain: "runtime", payload: { phase } });
  }

  getLifecycle(): RuntimeLifecyclePhase {
    return this.phase;
  }

  async dispatch<T>(event: Omit<RuntimeEvent<T>, "at">) {
    const full: RuntimeEvent<T> = { ...event, at: new Date().toISOString() };
    this.hooks.forEach((h) => h.onEvent?.(full as RuntimeEvent));

    const runMiddlewares = async (index: number) => {
      if (index >= this.middlewares.length) {
        this.listeners.get(event.type)?.forEach((fn) => fn(full as RuntimeEvent));
        this.listeners.get("*")?.forEach((fn) => fn(full as RuntimeEvent));
        return;
      }
      const mw = this.middlewares[index];
      await mw(full as RuntimeEvent, () => runMiddlewares(index + 1));
    };
    await runMiddlewares(0);
  }

  /** Coordinate multiple runtime domains in one orchestrated action. */
  async coordinate(action: string, domains: string[], fn: () => Promise<void>) {
    await this.dispatch({ type: "coordinate.start", domain: "runtime", payload: { action, domains } });
    try {
      await fn();
      await this.dispatch({ type: "coordinate.done", domain: "runtime", payload: { action, domains } });
    } catch (err) {
      await this.dispatch({
        type: "coordinate.error",
        domain: "runtime",
        payload: { action, error: err instanceof Error ? err.message : "unknown" },
      });
      throw err;
    }
  }
}

export const runtimeBus = new RuntimeBus();
