"use client";

import * as React from "react";
import { parseWorkflowSchema, type WorkflowSchema } from "@zhenhang/workflow-schema";
import { createWorkflowRuntime } from "@zhenhang/workflow-runtime";
import {
  StatusBadge,
  WorkspaceToolbarButton,
  designTokens,
  interactionTokens,
  typography,
  workflowStateToStatus,
  type InteractionStatus,
} from "@zhenhang/ui";

const ACTION_STATUS: Record<string, InteractionStatus> = {
  approve: "success",
  reject: "danger",
  submit: "processing",
};

export function WorkflowTimeline({
  records,
  canOperate,
  onOperate,
  pending,
}: {
  records: Array<{ actor: string; action: string; at: string; comment?: string }>;
  canOperate?: boolean;
  onOperate?: (action: "approve" | "reject") => void;
  pending?: boolean;
}) {
  if (!records.length) {
    return (
      <p className={typography.caption} style={{ color: designTokens.colors.text.muted }}>
        暂无审批记录
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {records.map((r, idx) => {
        const actionKey = r.action.toLowerCase();
        const status =
          ACTION_STATUS[actionKey] ??
          (actionKey.includes("reject") ? "danger" : actionKey.includes("approve") ? "success" : "info");
        return (
          <div
            key={`${r.at}-${idx}`}
            className="rounded border px-2 py-2 text-xs"
            style={{
              borderColor: designTokens.colors.border.default,
              borderLeftWidth: 3,
              borderLeftColor: designTokens.colors.primary.default,
              backgroundColor: designTokens.colors.background.subtle,
              minHeight: interactionTokens.controlHeight.tableRow,
            }}
          >
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={status} label={r.action} compact />
              <span className={typography.caption}>{r.actor}</span>
              <span className={typography.monoNumber}>{r.at}</span>
            </div>
            {r.comment ? (
              <p className={`${typography.body} mt-1`} style={{ color: designTokens.colors.text.secondary }}>
                {r.comment}
              </p>
            ) : null}
          </div>
        );
      })}
      {canOperate ? (
        <div className="flex gap-2 pt-1">
          <WorkspaceToolbarButton variant="primary" loading={pending} onClick={() => onOperate?.("approve")}>
            批准
          </WorkspaceToolbarButton>
          <WorkspaceToolbarButton variant="danger" loading={pending} onClick={() => onOperate?.("reject")}>
            驳回
          </WorkspaceToolbarButton>
        </div>
      ) : null}
    </div>
  );
}

const STATE_LABELS: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
  rejected: "已驳回",
};

export function WorkflowStateFlow({ states, current }: { states: string[]; current: string }) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {states.map((s, idx) => {
        const active = s === current;
        const status = workflowStateToStatus(s);
        return (
          <React.Fragment key={s}>
            <StatusBadge
              status={active ? status : "idle"}
              label={STATE_LABELS[s] ?? s}
              compact
              pulse={active && status === "processing"}
            />
            {idx < states.length - 1 ? (
              <span style={{ color: designTokens.colors.text.muted }}>›</span>
            ) : null}
          </React.Fragment>
        );
      })}
    </div>
  );
}

export function WorkflowSchemaView({
  schema,
  userPermissions,
  currentState,
}: {
  schema: WorkflowSchema | unknown;
  userPermissions: string[];
  currentState?: string;
}) {
  const parsed = parseWorkflowSchema(schema);
  const runtime = createWorkflowRuntime(parsed);
  const state = currentState ?? parsed.states[0]?.code ?? "";
  const ctx = { currentState: state, userPermissions };
  const actions = runtime.getAvailableActions(ctx);
  return (
    <div
      className="space-y-3 rounded border"
      style={{
        borderColor: designTokens.colors.border.default,
        backgroundColor: designTokens.colors.background.elevated,
        padding: interactionTokens.layout.panelPadding,
      }}
    >
      <WorkflowStateFlow states={parsed.states.map((s) => s.code)} current={state} />
      <div className="flex flex-wrap gap-1">
        {parsed.actions.map((a) => {
          const allowed = actions.some((x) => x.code === a.code);
          return (
            <StatusBadge key={a.code} status={allowed ? "info" : "idle"} label={a.label} compact />
          );
        })}
      </div>
    </div>
  );
}

export { createWorkflowRuntime } from "@zhenhang/workflow-runtime";
