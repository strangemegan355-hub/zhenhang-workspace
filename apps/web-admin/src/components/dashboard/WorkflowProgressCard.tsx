"use client";

import { CheckCircle2, Circle, Clock3 } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import type { PipelineItem, WorkflowNode } from "./types";

function buildWorkflowNodes(pipeline: PipelineItem[]): WorkflowNode[] {
  const reviewing = pipeline.find((p) => p.state === "reviewing")?.count ?? 0;
  const approved = pipeline.find((p) => p.state === "approved")?.count ?? 0;
  const draft = pipeline.find((p) => p.state === "draft")?.count ?? 0;
  const inFlow = reviewing > 0 || approved > 0;
  return [
    { key: "start", label: "发起", approver: "业务员", time: draft > 0 ? "进行中" : "已完成", state: inFlow || approved > 0 ? "done" : draft > 0 ? "active" : "pending" },
    { key: "dept", label: "部门审批", approver: "部门经理", time: reviewing > 0 ? "处理中" : approved > 0 ? "已通过" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "active" : "pending" },
    { key: "gm", label: "总经理审批", approver: "总经理", time: reviewing > 0 ? "排队中" : approved > 0 ? "已通过" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "active" : "pending" },
    { key: "finance", label: "财务审批", approver: "财务", time: approved > 0 ? "已通过" : undefined, state: approved > 0 ? "done" : reviewing > 0 ? "pending" : "pending" },
    { key: "done", label: "完成", approver: "系统", time: approved > 0 ? `\${approved} 单` : undefined, state: approved > 0 ? "done" : "pending" },
  ];
}

function NodeIcon({ state }: { state: WorkflowNode["state"] }) {
  if (state === "done") return <CheckCircle2 className="h-5 w-5 text-[var(--color-success)]" />;
  if (state === "active") return <Clock3 className="h-5 w-5 animate-pulse text-[var(--color-primary)]" />;
  return <Circle className="h-5 w-5 text-[var(--color-border)]" />;
}

export function WorkflowProgressCard({ pipeline }: { pipeline: PipelineItem[] }) {
  const nodes = buildWorkflowNodes(pipeline);
  return (
    <DashboardCard title="审批流程进度">
      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-[640px] items-start justify-between gap-2">
          {nodes.map((node, idx) => (
            <div key={node.key} className="flex flex-1 flex-col items-center">
              <div className="relative flex w-full items-center justify-center">
                {idx > 0 ? <div className={`absolute right-1/2 top-1/2 h-0.5 w-full -translate-y-1/2 \${node.state === "pending" && nodes[idx - 1]?.state === "pending" ? "bg-[var(--color-border)]" : "bg-[var(--color-primary)]/40"}`} style={{ width: "100%", left: "-50%" }} /> : null}
                <div className={`relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 bg-[var(--color-surface)] \${node.state === "done" ? "border-[var(--color-success)]" : node.state === "active" ? "border-[var(--color-primary)]" : "border-[var(--color-border)]"}`}><NodeIcon state={node.state} /></div>
              </div>
              <p className="mt-2 text-center text-xs font-semibold text-[var(--color-text)]">{node.label}</p>
              <p className="mt-0.5 text-center text-[10px] text-[var(--color-text-muted)]">{node.approver}</p>
              {node.time ? <p className="mt-0.5 text-center text-[10px] font-medium text-[var(--color-primary)]">{node.time}</p> : null}
            </div>
          ))}
        </div>
      </div>
    </DashboardCard>
  );
}
