import { runtimeTelemetry } from "@zhenhang/runtime-telemetry";

export type ClusterNode = {
  id: string;
  host?: string;
  healthy: boolean;
  lastHeartbeat: string;
  role?: "leader" | "follower";
};

export type CoordinationMessage = {
  type: "heartbeat" | "elect" | "lock_acquire" | "lock_release";
  nodeId: string;
  payload?: Record<string, unknown>;
  at: string;
};

/** Distributed coordination — leader election, locks, membership, health. */
export class DistributedCoordination {
  private nodes = new Map<string, ClusterNode>();
  private leaderId: string | null = null;
  private locks = new Map<string, { holder: string; expiresAt: number }>();
  private localNodeId: string;

  constructor(nodeId?: string) {
    this.localNodeId = nodeId ?? `node-${Date.now()}`;
    this.join(this.localNodeId);
  }

  getLocalNodeId() {
    return this.localNodeId;
  }

  join(nodeId: string, host?: string) {
    this.nodes.set(nodeId, {
      id: nodeId,
      host,
      healthy: true,
      lastHeartbeat: new Date().toISOString(),
      role: nodeId === this.leaderId ? "leader" : "follower",
    });
  }

  heartbeat(nodeId: string) {
    const node = this.nodes.get(nodeId);
    if (node) {
      node.lastHeartbeat = new Date().toISOString();
      node.healthy = true;
    }
  }

  /** Simple leader election — lowest healthy node id wins. */
  electLeader(): string | null {
    const healthy = [...this.nodes.values()].filter((n) => n.healthy);
    if (!healthy.length) return null;
    healthy.sort((a, b) => a.id.localeCompare(b.id));
    this.leaderId = healthy[0].id;
    for (const n of this.nodes.values()) {
      n.role = n.id === this.leaderId ? "leader" : "follower";
    }
    runtimeTelemetry.log("info", "coordination.leader.elected", { leaderId: this.leaderId });
    return this.leaderId;
  }

  getLeaderId() {
    return this.leaderId;
  }

  isLeader(nodeId = this.localNodeId) {
    return this.leaderId === nodeId;
  }

  /** Distributed lock with TTL (in-memory; Redis-backed in production). */
  acquireLock(resource: string, ttlMs = 30000): boolean {
    const now = Date.now();
    const existing = this.locks.get(resource);
    if (existing && existing.expiresAt > now && existing.holder !== this.localNodeId) {
      return false;
    }
    this.locks.set(resource, { holder: this.localNodeId, expiresAt: now + ttlMs });
    return true;
  }

  releaseLock(resource: string): boolean {
    const lock = this.locks.get(resource);
    if (!lock || lock.holder !== this.localNodeId) return false;
    this.locks.delete(resource);
    return true;
  }

  getMembership(): ClusterNode[] {
    return [...this.nodes.values()];
  }

  markUnhealthy(nodeId: string) {
    const node = this.nodes.get(nodeId);
    if (node) node.healthy = false;
  }

  protocol(message: CoordinationMessage) {
    switch (message.type) {
      case "heartbeat":
        this.heartbeat(message.nodeId);
        break;
      case "elect":
        this.electLeader();
        break;
      case "lock_acquire":
        if (message.payload?.resource) this.acquireLock(String(message.payload.resource));
        break;
      case "lock_release":
        if (message.payload?.resource) this.releaseLock(String(message.payload.resource));
        break;
    }
  }

  status() {
    return {
      localNodeId: this.localNodeId,
      leaderId: this.leaderId,
      members: this.getMembership().length,
      locks: this.locks.size,
    };
  }
}

export const distributedCoordination = new DistributedCoordination();
