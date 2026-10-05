"use client";

import * as React from "react";
import { WorkflowStateFlow, WorkflowTimeline } from "@zhenhang/workflow-ui";
import {
  StatusBadge,
  SystemPill,
  WorkspaceToolbarButton,
  designTokens,
  interactionTokens,
  typography,
  useIndustrialShortcuts,
  workflowStateToStatus,
} from "@zhenhang/ui";
import type { ApprovalRecordView, WorkflowActionOption } from "./types";

const QUICK_COMMENTS = ["同意，请继续", "价格需复核", "BOM 已确认", "驳回，补充成本依据"];

export function ApprovalUxPanel({
  workflowState,
  actions,
  records,
  onTransition,
  pending,
}: {
  workflowState: string;
  actions: WorkflowActionOption[];
  records: ApprovalRecordView[];
  onTransition: (actionCode: string, comment?: string) => void;
  pending?: boolean;
}) {
  const [comment, setComment] = React.useState("");
  const approveAction = actions.find((a) => a.action_code === "approve");
  const rejectAction = actions.find((a) => a.action_code === "reject");

  const fire = React.useCallback(
    (code: string, c?: string) => {
      onTransition(code, (c ?? comment) || undefined);
      setComment("");
    },
    [comment, onTransition],
  );

  useIndustrialShortcuts([
    {
      id: "approve-enter",
      key: "Enter",
      ctrl: true,
      enabled: Boolean(approveAction) && !pending,
      handler: () => fire("approve"),
    },
    {
      id: "reject-shift-r",
      key: "r",
      ctrl: true,
      shift: true,
      enabled: Boolean(rejectAction) && !pending,
      handler: () => fire("reject"),
    },
  ]);

  return (
    <div className="space-y-3" style={{ padding: interactionTokens.layout.panelPadding }}>
      <div className="flex items-center justify-between">
        <span className={typography.cardTitle}>快速审批</span>
        <SystemPill status="info" mono>
          Ctrl+Enter
        </SystemPill>
      </div>

      <WorkflowStateFlow states={["draft", "reviewing", "approved"]} current={workflowState} />

      <StatusBadge
        status={workflowStateToStatus(workflowState)}
        label={`当前 · ${workflowState}`}
        compact
        pulse={workflowState === "reviewing"}
      />

      {actions.length ? (
        <>
          <div className="flex flex-wrap gap-1">
            {QUICK_COMMENTS.map((q) => (
              <button
                key={q}
                type="button"
                className="rounded border px-2 py-0.5 text-[10px] transition"
                style={{
                  borderColor: designTokens.colors.border.default,
                  color: designTokens.colors.text.secondary,
                  transition: `border-color ${interactionTokens.transition.fast}, background-color ${interactionTokens.transition.fast}`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = interactionTokens.hover.bg;
                  e.currentTarget.style.borderColor = interactionTokens.hover.borderEmphasis;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.borderColor = designTokens.colors.border.default;
                }}
                onClick={() => setComment(q)}
              >
                {q}
              </button>
            ))}
          </div>
          <textarea
            className="w-full rounded border px-2 py-1.5 text-sm"
            style={{
              height: interactionTokens.controlHeight.input * 2,
              borderColor: designTokens.colors.border.default,
              backgroundColor: designTokens.colors.background.subtle,
              color: designTokens.colors.text.primary,
            }}
            rows={2}
            placeholder="审批意见"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            {approveAction ? (
              <WorkspaceToolbarButton
                variant="primary"
                loading={pending}
                disabled={pending}
                onClick={() => fire("approve")}
              >
                ✓ {approveAction.action_name}
              </WorkspaceToolbarButton>
            ) : null}
            {rejectAction ? (
              <WorkspaceToolbarButton
                variant="danger"
                loading={pending}
                disabled={pending}
                onClick={() => fire("reject")}
              >
                ✕ {rejectAction.action_name}
              </WorkspaceToolbarButton>
            ) : null}
          </div>
          {actions
            .filter((a) => !["approve", "reject"].includes(a.action_code))
            .map((a) => (
              <WorkspaceToolbarButton
                key={a.action_code}
                disabled={pending}
                onClick={() => fire(a.action_code)}
              >
                {a.action_name}
              </WorkspaceToolbarButton>
            ))}
        </>
      ) : (
        <p className={typography.caption} style={{ color: designTokens.colors.text.muted }}>
          当前状态无可用操作
        </p>
      )}

      <WorkflowTimeline records={records} pending={pending} />
    </div>
  );
}
