import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type ConsensusState = {
  term: number;
  leaderId: string | null;
  leaseExpiresAt: number;
  quorumSize: number;
  votes: Map<string, boolean>;
};

/** Consensus coordination — term, lease, quorum, fencing, leader failover. */
export class ConsensusCoordination {
  private term = 0;
  private leaderId: string | null = null;
  private leaseExpiresAt = 0;
  private quorumSize = 1;
  private votes = new Map<string, boolean>();
  private fencingToken = 0;
  private nodeId: string;

  constructor(nodeId?: string, quorumSize = 1) {
    this.nodeId = nodeId ?? `node-${Date.now()}`;
    this.quorumSize = quorumSize;
  }

  getState(): ConsensusState {
    return {
      term: this.term,
      leaderId: this.leaderId,
      leaseExpiresAt: this.leaseExpiresAt,
      quorumSize: this.quorumSize,
      votes: new Map(this.votes),
    };
  }

  startTerm(): number {
    this.term += 1;
    this.votes.clear();
    this.leaderId = null;
    runtimeTelemetry.log("info", "consensus.term.start", { term: this.term });
    return this.term;
  }

  vote(candidateId: string, granted: boolean) {
    this.votes.set(candidateId, granted);
  }

  hasQuorum(): boolean {
    const yes = [...this.votes.values()].filter(Boolean).length;
    return yes >= Math.ceil(this.quorumSize / 2);
  }

  electLeader(candidateId: string, leaseMs = 30_000): boolean {
    if (!this.hasQuorum() && this.quorumSize > 1) return false;
    this.leaderId = candidateId;
    this.leaseExpiresAt = Date.now() + leaseMs;
    this.fencingToken += 1;
    runtimeTelemetry.log("info", "consensus.leader", { leaderId: candidateId, term: this.term });
    return true;
  }

  isLeaseValid(): boolean {
    return this.leaderId !== null && Date.now() < this.leaseExpiresAt;
  }

  getFencingToken(): number {
    return this.fencingToken;
  }

  validateFencing(token: number): boolean {
    return token === this.fencingToken && this.isLeaseValid();
  }

  /** Leader failover when lease expires. */
  failover(nextLeaderId: string): boolean {
    if (this.isLeaseValid() && this.leaderId !== this.nodeId) return false;
    this.startTerm();
    this.vote(nextLeaderId, true);
    return this.electLeader(nextLeaderId);
  }

  isLeader(nodeId = this.nodeId): boolean {
    return this.leaderId === nodeId && this.isLeaseValid();
  }
}

export const consensusCoordination = new ConsensusCoordination();
