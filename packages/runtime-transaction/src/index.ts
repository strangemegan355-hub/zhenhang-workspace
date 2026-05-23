import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type TxPhase = "prepare" | "commit" | "abort";
export type TxState = "pending" | "prepared" | "committed" | "aborted";

export type TransactionRecord = {
  id: string;
  state: TxState;
  participants: string[];
  events: string[];
  snapshotId?: string;
  at: string;
};

/** Runtime transaction layer — 2PC, snapshot/recovery transactions, transactional replay. */
export class RuntimeTransactionLayer {
  private transactions = new Map<string, TransactionRecord>();
  private eventCommitState = new Map<string, TxState>();
  private replayCursor = new Map<string, number>();

  begin(participants: string[]): TransactionRecord {
    const tx: TransactionRecord = {
      id: `tx-${Date.now()}`,
      state: "pending",
      participants,
      events: [],
      at: new Date().toISOString(),
    };
    this.transactions.set(tx.id, tx);
    runtimeTelemetry.log("info", "tx.begin", { id: tx.id });
    return tx;
  }

  /** Phase 1 — prepare all participants. */
  async prepare(txId: string, prepareFns: Array<() => Promise<boolean>>): Promise<boolean> {
    const tx = this.transactions.get(txId);
    if (!tx) return false;
    const results = await Promise.all(prepareFns.map((fn) => fn()));
    const ok = results.every(Boolean);
    tx.state = ok ? "prepared" : "aborted";
    if (!ok) tx.state = "aborted";
    runtimeTelemetry.increment(ok ? "tx.prepare.ok" : "tx.prepare.fail");
    return ok;
  }

  /** Phase 2 — commit. */
  async commit(txId: string, commitFns: Array<() => Promise<void>>): Promise<boolean> {
    const tx = this.transactions.get(txId);
    if (!tx || tx.state !== "prepared") return false;
    await Promise.all(commitFns.map((fn) => fn()));
    tx.state = "committed";
    tx.events.forEach((eid) => this.eventCommitState.set(eid, "committed"));
    runtimeTelemetry.increment("tx.commit");
    return true;
  }

  abort(txId: string) {
    const tx = this.transactions.get(txId);
    if (!tx) return;
    tx.state = "aborted";
    tx.events.forEach((eid) => this.eventCommitState.set(eid, "aborted"));
  }

  attachEvent(txId: string, eventId: string) {
    const tx = this.transactions.get(txId);
    if (!tx) return;
    tx.events.push(eventId);
    this.eventCommitState.set(eventId, "pending");
  }

  /** Snapshot transaction — bind snapshot to tx. */
  bindSnapshot(txId: string, snapshotId: string) {
    const tx = this.transactions.get(txId);
    if (tx) tx.snapshotId = snapshotId;
  }

  /** Recovery transaction — replay committed events from cursor. */
  recoveryTransaction(txId: string): string[] {
    const tx = this.transactions.get(txId);
    if (!tx || tx.state !== "committed") return [];
    const cursor = this.replayCursor.get(txId) ?? 0;
    const slice = tx.events.slice(cursor);
    this.replayCursor.set(txId, tx.events.length);
    return slice;
  }

  transactionalReplay(txId: string, handler: (eventId: string) => void) {
    const events = this.recoveryTransaction(txId);
    events.forEach((eid) => {
      if (this.eventCommitState.get(eid) === "committed") handler(eid);
    });
  }

  getEventCommitState(eventId: string): TxState | undefined {
    return this.eventCommitState.get(eventId);
  }

  list(): TransactionRecord[] {
    return [...this.transactions.values()];
  }
}

export const runtimeTransaction = new RuntimeTransactionLayer();
