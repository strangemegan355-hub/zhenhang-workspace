"use client";

import {
  useApprovalActionMutation,
  useApprovalInboxQuery,
  type ApprovalTask,
} from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader } from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";
import { MasterListPage } from "@/components/master/master-list-page";
import { dangerActionClass, fieldInputClass, fieldLabelClass, linkActionClass } from "@/lib/form-styles";

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

type ApprovalDisplayRow = {
  id: string;
  taskId: string;
  type: string;
  title: string;
  submitter: string;
  amount: string;
  discount: string;
  submittedAt: string;
};

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
      const answer = window.prompt("驳回原因（可选）");
      if (answer === null) return;
      comment = answer || undefined;
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

  // Display-ready values, as the other list pages do: GridColumn cannot format a cell.
  const rows: ApprovalDisplayRow[] = useMemo(
    () =>
      filtered.map((task) => ({
        id: `${task.task_type}-${task.id}`,
        taskId: task.id,
        type: TASK_TYPE_LABEL[task.task_type] ?? task.task_type,
        title: task.subtitle ? `${task.title} · ${task.subtitle}` : task.title,
        submitter: task.submitter_name ?? "—",
        amount: task.amount != null ? money(task.amount) : "—",
        discount:
          task.discount_amount != null && Number(task.discount_amount) > 0
            ? `${money(task.discount_amount)} (${Number(task.discount_rate_pct ?? 0).toFixed(2)}%)`
            : "—",
        submittedAt: formatTime(task.submitted_at),
      })),
    [filtered],
  );

  return (
    <IndustrialPage gap="md" fill>
    <MasterListPage<ApprovalDisplayRow>
      title="待办列表"
      externalHeader={
        <>
          <PageHeader
            title="审批中心"
            subtitle={`待办 ${items.length} 条 · 在此通过/驳回即可，无需再到报价或采购页重复录入金额；详情链回原单据核对。`}
          />
          {actionError ? <p className="mb-2 text-xs text-[var(--color-danger)]">{actionError}</p> : null}
        </>
      }
      persistenceKey="approvals-v1"
      exportFilename="approvals"
      pageSize={50}
      columns={[
        { key: "type", title: "类型", canView: true, fixed: "left", width: 110 },
        { key: "title", title: "标题", canView: true },
        { key: "submitter", title: "提交人", canView: true, width: 110 },
        { key: "amount", title: "金额 (CNY)", canView: true, width: 120, align: "right" },
        { key: "discount", title: "优惠 (CNY)", canView: true, width: 150, align: "right" },
        { key: "submittedAt", title: "提交时间", canView: true, width: 140 },
      ]}
      rows={rows}
      total={rows.length}
      page={1}
      onPageChange={() => {}}
      search=""
      onSearchChange={() => {}}
      query={{
        isLoading: inboxQuery.isLoading,
        isError: inboxQuery.isError,
        isFetching: inboxQuery.isFetching,
        refetch: () => {
          void inboxQuery.refetch();
        },
      }}
      rowKey={(row) => row.id}
      emptyHint="暂无待审批任务"
      toolbarExtra={
        <label className="block space-y-1 text-xs">
          <span className={fieldLabelClass}>类型</span>
          <select className={fieldInputClass} value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">全部 ({items.length})</option>
            <option value="quote_receivable">应收优惠</option>
            <option value="procurement_payable">采购应付</option>
            <option value="quote_workflow">报价审批</option>
          </select>
        </label>
      }
      rowActions={(row) => {
        const task = filtered.find((item) => item.id === row.taskId);
        if (!task) return null;
        return (
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
        );
      }}
    />
    </IndustrialPage>
  );
}
