"use client";

import {
  useApprovalActionMutation,
  useApprovalInboxQuery,
  type ApprovalTask,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, PageHeader, WorkspaceToolbarButton } from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  dangerActionClass,
  fieldInputClass,
  fieldLabelClass,
  linkActionClass,
  tableBodyRowClass,
  tableHeaderRowClass,
} from "@/lib/form-styles";

const TASK_TYPE_LABEL: Record<string, string> = {
  quote_receivable: "应收优惠",
  quote_workflow: "报价审批",
  procurement_payable: "采购应付",
};

function money(n: number | string | null | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export default function ApprovalsPage() {
  const inboxQuery = useApprovalInboxQuery();
  const actionMutation = useApprovalActionMutation();
  const [filter, setFilter] = useState<string>("all");
  const [actionError, setActionError] = useState<string | null>(null);

  const items = useMemo(() => inboxQuery.data?.items ?? [], [inboxQuery.data]);
  const filtered = useMemo(
    () => (filter === "all" ? items : items.filter((i) => i.task_type === filter)),
    [items, filter],
  );

  const handleAction = async (task: ApprovalTask, action: "approve" | "reject") => {
    setActionError(null);
    let comment: string | undefined;
    if (action === "reject") {
      comment = window.prompt("驳回原因（可选）") ?? undefined;
      if (comment === null) return;
    } else if (!window.confirm(`确定通过「${task.title}」吗？`)) {
      return;
    }
    try {
      await actionMutation.mutateAsync({
        task_type: task.task_type,
        task_id: task.id,
        action,
        comment,
      });
      void inboxQuery.refetch();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "操作失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="审批中心"
        subtitle="集中处理待办审批；后续采购、项目等审批也会汇总到此"
        actions={
          <WorkspaceToolbarButton loading={inboxQuery.isFetching} onClick={() => void inboxQuery.refetch()}>
            刷新
          </WorkspaceToolbarButton>
        }
      />

      <IndustrialPanel title="待办列表">
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>类型</span>
            <select className={fieldInputClass} value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">全部 ({items.length})</option>
              <option value="quote_receivable">应收优惠</option>
              <option value="procurement_payable">采购应付</option>
              <option value="quote_workflow">报价审批</option>
            </select>
          </label>
        </div>

        {actionError ? <p className="mb-2 text-xs text-red-500">{actionError}</p> : null}

        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-2 py-2 text-left font-normal">类型</th>
                <th className="px-2 py-2 text-left font-normal">标题</th>
                <th className="px-2 py-2 text-left font-normal">提交人</th>
                <th className="px-2 py-2 text-left font-normal">金额</th>
                <th className="px-2 py-2 text-left font-normal">优惠</th>
                <th className="px-2 py-2 text-left font-normal">提交时间</th>
                <th className="px-2 py-2 text-left font-normal">操作</th>
              </tr>
            </thead>
            <tbody>
              {inboxQuery.isLoading ? (
                <tr>
                  <td colSpan={7} className="px-2 py-8 text-center text-[var(--color-text-muted)]">
                    加载中…
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-2 py-8 text-center text-[var(--color-text-muted)]">
                    暂无待审批任务
                  </td>
                </tr>
              ) : (
                filtered.map((task) => (
                  <tr key={`${task.task_type}-${task.id}`} className={tableBodyRowClass}>
                    <td className="px-2 py-2">
                      <span className="rounded bg-[var(--color-primary-soft)] px-1.5 py-0.5 text-[10px] text-[var(--color-primary)]">
                        {TASK_TYPE_LABEL[task.task_type] ?? task.task_type}
                      </span>
                    </td>
                    <td className="px-2 py-2">
                      <div className="font-medium text-[var(--color-text)]">{task.title}</div>
                      {task.subtitle ? (
                        <div className="text-[10px] text-[var(--color-text-muted)]">{task.subtitle}</div>
                      ) : null}
                    </td>
                    <td className="px-2 py-2">{task.submitter_name ?? "—"}</td>
                    <td className="px-2 py-2">{task.amount != null ? money(task.amount) : "—"}</td>
                    <td className="px-2 py-2 text-amber-600">
                      {task.discount_amount != null && Number(task.discount_amount) > 0
                        ? `${money(task.discount_amount)} (${Number(task.discount_rate_pct ?? 0).toFixed(2)}%)`
                        : "—"}
                    </td>
                    <td className="px-2 py-2">{formatTime(task.submitted_at)}</td>
                    <td className="px-2 py-2">
                      <div className="flex flex-wrap gap-2">
                        {task.detail_href ? (
                          <Link href={task.detail_href} className={linkActionClass}>
                            详情
                          </Link>
                        ) : null}
                        <button
                          type="button"
                          className={linkActionClass}
                          disabled={actionMutation.isPending}
                          onClick={() => void handleAction(task, "approve")}
                        >
                          通过
                        </button>
                        <button
                          type="button"
                          className={dangerActionClass}
                          disabled={actionMutation.isPending}
                          onClick={() => void handleAction(task, "reject")}
                        >
                          驳回
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </IndustrialPanel>
    </IndustrialPage>
  );
}
