"use client";

import { IndustrialPanel, RealtimeDot, StatusBadge, typography, workflowStateToStatus } from "@zhenhang/ui";
import Link from "next/link";

const MOCK_LINES = [
  { id: "l1", name: "产线 A", status: "running", oee: 87 },
  { id: "l2", name: "产线 B", status: "idle", oee: 72 },
  { id: "l3", name: "产线 C", status: "alarm", oee: 61 },
];

const STATUS_TEXT: Record<string, string> = {
  running: "运行",
  idle: "待机",
  alarm: "告警",
};

export function WorkshopStatusPanel() {
  return (
    <IndustrialPanel
      title="车间状态"
      toolbar={<span className={typography.caption}>演示数据</span>}
    >
      <ul className="space-y-2">
        {MOCK_LINES.map((line) => (
          <li
            key={line.id}
            className="flex items-center justify-between rounded px-2 py-2 transition hover:bg-[#1a2332]"
            style={{ minHeight: 32 }}
          >
            <div className="flex items-center gap-2">
              <RealtimeDot
                level={line.status === "running" ? "ok" : line.status === "alarm" ? "error" : "warn"}
                label={line.name}
              />
              <StatusBadge
                status={workflowStateToStatus(line.status === "running" ? "approved" : line.status === "alarm" ? "rejected" : "draft")}
                label={STATUS_TEXT[line.status] ?? line.status}
                compact
              />
            </div>
            <span className={typography.monoNumber}>OEE {line.oee}%</span>
          </li>
        ))}
      </ul>
      <Link href="/workshop" className={`${typography.caption} mt-3 inline-block text-blue-500 hover:underline`}>
        车间看板 →
      </Link>
    </IndustrialPanel>
  );
}
