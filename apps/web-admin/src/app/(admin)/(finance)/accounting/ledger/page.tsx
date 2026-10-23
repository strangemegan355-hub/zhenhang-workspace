"use client";

import {
  useAccountingStatusQuery,
  useCreateLedgerReceiptMutation,
  useCreateLedgerReceivableMutation,
  useCustomerLedgerDetailQuery,
  useCustomersQuery,
  useLedgerCustomersQuery,
  useRegisterLedgerCustomerMutation,
  type CustomerLedgerSummary,
  type LedgerEntry,
} from "@zhenhang/query-hooks";
import {
  FilterBar,
  IndustrialPage,
  IndustrialPanel,
  PageHeader,
  WorkspaceToolbarButton,
} from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  fieldInputClass,
  fieldLabelClass,
  filterCheckClass,
  filterFieldClass,
  formPanelClass,
  linkActionClass,
  moneyCellClass,
  tableBodyRowClass,
  tableHeaderRowClass,
} from "@/lib/form-styles";
import { FinanceSubNav } from "@/components/finance/finance-sub-nav";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";

const PAYMENT_STATUS_LABEL: Record<string, string> = {
  unpaid: "未支付",
  partial: "部分支付",
  paid: "支付完成",
};

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

type AllocationRow = { receivable_entry_id: string; amount: string };

const defaultBillForm = {
  amount: "",
  occurred_on: todayInputValue(),
  title: "",
  remark: "",
};

export default function AccountingLedgerPage() {
  const user = useAuthStore((s) => s.user);
  const perms = user?.permissions ?? [];
  const canCreate = hasPermission(perms, "business:accounting:create");
  const canBackfill = hasPermission(perms, "business:accounting:backfill");
  const canReceipt = hasPermission(perms, "business:accounting:confirm");

  const statusQuery = useAccountingStatusQuery();
  const enabled = statusQuery.data?.flags.accounting_enabled ?? false;

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [selectedCustomerName, setSelectedCustomerName] = useState("");

  const [showAddCustomer, setShowAddCustomer] = useState(false);
  const [addCustomerId, setAddCustomerId] = useState("");

  const [showReceipt, setShowReceipt] = useState(false);
  const [showBillForm, setShowBillForm] = useState(false);
  const [billForm, setBillForm] = useState(defaultBillForm);
  const [receiptForm, setReceiptForm] = useState({
    amount: "",
    occurred_on: todayInputValue(),
    title: "客户收款",
    remark: "",
  });
  const [allocations, setAllocations] = useState<AllocationRow[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  const customersQuery = useLedgerCustomersQuery(
    page,
    { outstandingOnly, q: search.trim() || undefined },
    enabled && !selectedCustomerId,
  );
  const masterCustomersQuery = useCustomersQuery(1);
  const detailQuery = useCustomerLedgerDetailQuery(selectedCustomerId, enabled && Boolean(selectedCustomerId));
  const receiptMutation = useCreateLedgerReceiptMutation();
  const registerMutation = useRegisterLedgerCustomerMutation();
  const billMutation = useCreateLedgerReceivableMutation();

  const customerRows = useMemo(() => {
    const items = (customersQuery.data as { items?: CustomerLedgerSummary[] } | undefined)?.items ?? [];
    return items.map((c) => ({
      id: c.customer_id,
      name: c.customer_name,
      code: c.customer_code ?? "",
      receivableTotal: money(c.receivable_total),
      receivedTotal: money(c.received_total),
      outstandingTotal: money(c.outstanding_total),
      openBillCount: c.open_bill_count,
      lastDate: c.last_occurred_on ?? "—",
    }));
  }, [customersQuery.data]);

  const ledgerCustomerIds = useMemo(() => new Set(customerRows.map((c) => c.id)), [customerRows]);

  const addableCustomers = useMemo(() => {
    const items = (masterCustomersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];
    return items
      .filter((c) => !ledgerCustomerIds.has(String(c.id ?? "")))
      .map((c) => ({ value: String(c.id ?? ""), label: `${String(c.name ?? "")}${c.code ? ` (${String(c.code)})` : ""}` }));
  }, [masterCustomersQuery.data, ledgerCustomerIds]);

  const customerTotal = (customersQuery.data as { total?: number } | undefined)?.total ?? customerRows.length;

  const detail = detailQuery.data;
  const openReceivables = useMemo(() => detail?.open_receivables ?? [], [detail]);

  const outstandingRows = useMemo(
    () =>
      openReceivables.map((row: LedgerEntry) => ({
        id: row.id,
        entryNo: row.entry_no,
        sourceLabel: row.source_label,
        title: row.title,
        occurredOn: row.occurred_on,
        amount: money(row.amount),
        openAmount: money(row.open_amount),
        paymentStatus: row.payment_status ? PAYMENT_STATUS_LABEL[row.payment_status] ?? row.payment_status : "—",
      })),
    [openReceivables],
  );

  const timelineRows = useMemo(() => {
    return (detail?.timeline ?? []).map((row: LedgerEntry) => ({
      id: row.id,
      entryNo: row.entry_no,
      entryKind: row.entry_kind,
      sourceLabel: row.source_label,
      title: row.title,
      occurredOn: row.occurred_on,
      amount: money(row.amount),
      openAmount: money(row.open_amount),
      paymentStatus: row.payment_status ? PAYMENT_STATUS_LABEL[row.payment_status] ?? row.payment_status : "—",
      allocations: row.allocations ?? [],
    }));
  }, [detail]);

  const allocSum = allocations.reduce((s, a) => s + (Number(a.amount) || 0), 0);
  const receiptAmount = Number(receiptForm.amount) || 0;

  const openDetail = (id: string, name: string) => {
    setSelectedCustomerId(id);
    setSelectedCustomerName(name);
    setShowReceipt(false);
    setShowBillForm(false);
    setFormError(null);
  };

  const backToList = () => {
    setSelectedCustomerId(null);
    setSelectedCustomerName("");
    setShowReceipt(false);
    setShowBillForm(false);
    setFormError(null);
  };

  const initReceiptForm = () => {
    setReceiptForm({ amount: "", occurred_on: todayInputValue(), title: "客户收款", remark: "" });
    setAllocations(
      openReceivables.slice(0, 1).map((r) => ({
        receivable_entry_id: r.id,
        amount: String(r.open_amount),
      })),
    );
    setFormError(null);
  };

  const handleAddCustomer = async () => {
    setFormError(null);
    if (!addCustomerId) {
      setFormError("请选择客户");
      return;
    }
    try {
      const row = await registerMutation.mutateAsync(addCustomerId);
      setShowAddCustomer(false);
      setAddCustomerId("");
      void customersQuery.refetch();
      openDetail(row.customer_id, row.customer_name);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "添加客户失败");
    }
  };

  const handleCreateBill = async () => {
    setFormError(null);
    if (!selectedCustomerId) return;
    if (!billForm.title.trim()) {
      setFormError("请填写账单摘要");
      return;
    }
    if (!billForm.amount || Number(billForm.amount) <= 0) {
      setFormError("请填写有效金额");
      return;
    }
    try {
      await billMutation.mutateAsync({
        customerId: selectedCustomerId,
        body: {
          amount: Number(billForm.amount),
          occurred_on: billForm.occurred_on,
          title: billForm.title.trim(),
          remark: billForm.remark.trim() || undefined,
          is_backfill: canBackfill && billForm.occurred_on < todayInputValue(),
        },
      });
      setBillForm(defaultBillForm);
      setShowBillForm(false);
      void detailQuery.refetch();
      void customersQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "录入账单失败");
    }
  };

  const handleReceipt = async () => {
    setFormError(null);
    if (!selectedCustomerId) return;
    if (!receiptForm.title.trim()) {
      setFormError("请填写摘要");
      return;
    }
    if (receiptAmount <= 0) {
      setFormError("请填写有效收款金额");
      return;
    }
    if (allocations.length === 0) {
      setFormError("请至少选择一笔应收进行核销");
      return;
    }
    for (const a of allocations) {
      if (!a.receivable_entry_id || Number(a.amount) <= 0) {
        setFormError("核销明细填写不完整");
        return;
      }
    }
    if (Math.abs(allocSum - receiptAmount) > 0.001) {
      setFormError("核销合计必须等于收款金额");
      return;
    }
    try {
      await receiptMutation.mutateAsync({
        customer_id: selectedCustomerId,
        amount: receiptAmount,
        occurred_on: receiptForm.occurred_on,
        title: receiptForm.title.trim(),
        remark: receiptForm.remark.trim() || undefined,
        allocations: allocations.map((a) => ({
          receivable_entry_id: a.receivable_entry_id,
          amount: Number(a.amount),
        })),
      });
      setShowReceipt(false);
      void detailQuery.refetch();
      void customersQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "登记收款失败");
    }
  };

  if (!enabled && !statusQuery.isLoading) {
    return (
      <IndustrialPage gap="md" fill>
        <PageHeader title="财务中心 · 客户应收" subtitle="记账功能未开启" />
        <FinanceSubNav />
        <IndustrialPanel>
          <p className="text-sm text-[var(--color-text-muted)]">
            请先在
            <Link href="/business-settings" className={`mx-1 ${linkActionClass}`}>
              业务设置
            </Link>
            中开启「记账功能」。试用环境请用 trialadmin 等具备业务设置权限的账号开启；开启后在此查看客户应收，勿重复手填客户。
          </p>
        </IndustrialPanel>
      </IndustrialPage>
    );
  }

  if (selectedCustomerId) {
    const detailError = detailQuery.isError
      ? detailQuery.error instanceof Error
        ? detailQuery.error.message
        : "加载明细失败"
      : null;

    return (
      <IndustrialPage gap="md" fill>
        <PageHeader
          title={`客户应收 · ${detail?.customer_name ?? selectedCustomerName}`}
          subtitle={detail?.customer_code ? `客户编码 ${detail.customer_code}` : "客户应收、收款与支付状态"}
          actions={
            <div className="flex flex-wrap gap-2">
              <WorkspaceToolbarButton onClick={backToList}>返回客户列表</WorkspaceToolbarButton>
              {canCreate ? (
                <WorkspaceToolbarButton
                  onClick={() => {
                    setShowBillForm((v) => !v);
                    setShowReceipt(false);
                    setFormError(null);
                  }}
                >
                  {showBillForm ? "取消录入" : "录入账单"}
                </WorkspaceToolbarButton>
              ) : null}
              {canReceipt && openReceivables.length > 0 ? (
                <WorkspaceToolbarButton
                  onClick={() => {
                    initReceiptForm();
                    setShowReceipt((v) => !v);
                    setShowBillForm(false);
                  }}
                >
                  {showReceipt ? "取消收款" : "登记收款"}
                </WorkspaceToolbarButton>
              ) : null}
            </div>
          }
        />
        <FinanceSubNav />

        {detailError ? (
          <IndustrialPanel>
            <p className="text-sm text-[var(--color-danger)]">{detailError}</p>
          </IndustrialPanel>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <IndustrialPanel title="应收合计">
            <p className="text-xl font-semibold tabular-nums">{money(detail?.receivable_total)}</p>
          </IndustrialPanel>
          <IndustrialPanel title="已收合计">
            <p className="text-xl font-semibold tabular-nums">{money(detail?.received_total)}</p>
          </IndustrialPanel>
          <IndustrialPanel title="客户欠款">
            <p className="text-xl font-semibold tabular-nums text-[var(--color-warning)]">
              {money(detail?.outstanding_total)}
            </p>
          </IndustrialPanel>
          <IndustrialPanel title="未结清笔数">
            <p className="text-xl font-semibold tabular-nums">{detail?.open_bill_count ?? 0}</p>
          </IndustrialPanel>
        </div>

        {showBillForm && canCreate ? (
          <IndustrialPanel title="录入应收账单">
            <div className={`${formPanelClass} grid gap-3 md:grid-cols-2 lg:grid-cols-3`}>
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>账单金额 *</span>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  className={fieldInputClass}
                  value={billForm.amount}
                  onChange={(e) => setBillForm((s) => ({ ...s, amount: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>业务发生日 *</span>
                <input
                  type="date"
                  className={fieldInputClass}
                  max={todayInputValue()}
                  value={billForm.occurred_on}
                  onChange={(e) => setBillForm((s) => ({ ...s, occurred_on: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs md:col-span-2">
                <span className={fieldLabelClass}>账单摘要 *</span>
                <input
                  className={fieldInputClass}
                  placeholder="如：设备维修费、配件款"
                  value={billForm.title}
                  onChange={(e) => setBillForm((s) => ({ ...s, title: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs md:col-span-2">
                <span className={fieldLabelClass}>备注</span>
                <input
                  className={fieldInputClass}
                  value={billForm.remark}
                  onChange={(e) => setBillForm((s) => ({ ...s, remark: e.target.value }))}
                />
              </label>
            </div>
            {canBackfill && billForm.occurred_on < todayInputValue() ? (
              <p className="mt-2 text-[10px] text-[var(--color-text-muted)]">历史日期将按补录账处理，入账日为今天。</p>
            ) : null}
            {formError ? <p className="mt-3 text-xs text-[var(--color-danger)]">{formError}</p> : null}
            <div className="mt-4">
              <WorkspaceToolbarButton onClick={() => void handleCreateBill()} disabled={billMutation.isPending}>
                {billMutation.isPending ? "提交中…" : "确认录入账单"}
              </WorkspaceToolbarButton>
            </div>
          </IndustrialPanel>
        ) : null}

        {showReceipt && canReceipt ? (
          <IndustrialPanel title="登记收款并核销">
            <div className={`${formPanelClass} grid gap-3 md:grid-cols-2 lg:grid-cols-3`}>
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>收款金额 *</span>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  className={fieldInputClass}
                  value={receiptForm.amount}
                  onChange={(e) => setReceiptForm((s) => ({ ...s, amount: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>业务发生日 *</span>
                <input
                  type="date"
                  className={fieldInputClass}
                  max={todayInputValue()}
                  value={receiptForm.occurred_on}
                  onChange={(e) => setReceiptForm((s) => ({ ...s, occurred_on: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs md:col-span-2">
                <span className={fieldLabelClass}>摘要 *</span>
                <input
                  className={fieldInputClass}
                  value={receiptForm.title}
                  onChange={(e) => setReceiptForm((s) => ({ ...s, title: e.target.value }))}
                />
              </label>
              <label className="block space-y-1 text-xs md:col-span-2">
                <span className={fieldLabelClass}>备注</span>
                <input
                  className={fieldInputClass}
                  value={receiptForm.remark}
                  onChange={(e) => setReceiptForm((s) => ({ ...s, remark: e.target.value }))}
                />
              </label>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-xs">
                <thead>
                  <tr className={tableHeaderRowClass}>
                    <th className="px-3 py-2">核销应收</th>
                    <th className="px-3 py-2">未收余额</th>
                    <th className="px-3 py-2">本次核销</th>
                    <th className="px-3 py-2 w-16" />
                  </tr>
                </thead>
                <tbody>
                  {allocations.map((row, idx) => {
                    const recv = openReceivables.find((r) => r.id === row.receivable_entry_id);
                    return (
                      <tr key={`${row.receivable_entry_id}-${idx}`} className={tableBodyRowClass}>
                        <td className="px-3 py-2">
                          <select
                            className={fieldInputClass}
                            value={row.receivable_entry_id}
                            onChange={(e) => {
                              const id = e.target.value;
                              const target = openReceivables.find((r) => r.id === id);
                              setAllocations((rows) =>
                                rows.map((r, i) =>
                                  i === idx
                                    ? { receivable_entry_id: id, amount: target ? String(target.open_amount) : "" }
                                    : r,
                                ),
                              );
                            }}
                          >
                            <option value="">选择应收</option>
                            {openReceivables.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.entry_no} · {r.title}（未收 {money(r.open_amount)}）
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2 tabular-nums">{recv ? money(recv.open_amount) : "—"}</td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            min={0}
                            step={0.01}
                            className={fieldInputClass}
                            value={row.amount}
                            onChange={(e) =>
                              setAllocations((rows) =>
                                rows.map((r, i) => (i === idx ? { ...r, amount: e.target.value } : r)),
                              )
                            }
                          />
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            className={linkActionClass}
                            onClick={() => setAllocations((rows) => rows.filter((_, i) => i !== idx))}
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
                <button
                  type="button"
                  className={linkActionClass}
                  onClick={() => setAllocations((rows) => [...rows, { receivable_entry_id: "", amount: "" }])}
                >
                  + 增加核销行
                </button>
                <span className="text-[var(--color-text-muted)]">
                  核销合计 {money(allocSum)} / 收款 {money(receiptAmount)}
                </span>
              </div>
            </div>

            {formError ? <p className="mt-3 text-xs text-[var(--color-danger)]">{formError}</p> : null}
            <div className="mt-4">
              <WorkspaceToolbarButton onClick={() => void handleReceipt()} disabled={receiptMutation.isPending}>
                {receiptMutation.isPending ? "提交中…" : "确认登记收款"}
              </WorkspaceToolbarButton>
            </div>
          </IndustrialPanel>
        ) : null}

        <IndustrialPanel title="欠款项目">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead>
                <tr className={tableHeaderRowClass}>
                  <th className="px-3 py-2">日期</th>
                  <th className="px-3 py-2">单号</th>
                  <th className="px-3 py-2">来源</th>
                  <th className="px-3 py-2">摘要</th>
                  <th className={`${moneyCellClass} !px-3`}>账单金额</th>
                  <th className={`${moneyCellClass} !px-3`}>未收</th>
                  <th className="px-3 py-2">状态</th>
                </tr>
              </thead>
              <tbody>
                {detailQuery.isLoading ? (
                  <tr className={tableBodyRowClass}>
                    <td colSpan={7} className="px-3 py-6 text-center text-[var(--color-text-muted)]">
                      加载中…
                    </td>
                  </tr>
                ) : outstandingRows.length === 0 ? (
                  <tr className={tableBodyRowClass}>
                    <td colSpan={7} className="px-3 py-6 text-center text-[var(--color-text-muted)]">
                      暂无欠款项目{canCreate ? "，可点击「录入账单」添加" : ""}
                    </td>
                  </tr>
                ) : (
                  outstandingRows.map((row) => (
                    <tr key={row.id} className={tableBodyRowClass}>
                      <td className="px-3 py-2">{row.occurredOn}</td>
                      <td className="px-3 py-2 font-mono text-[11px]">{row.entryNo}</td>
                      <td className="px-3 py-2">{row.sourceLabel}</td>
                      <td className="px-3 py-2">{row.title}</td>
                      <td className={`${moneyCellClass} !px-3`}>{row.amount}</td>
                      <td className={`${moneyCellClass} !px-3 text-[var(--color-warning)]`}>{row.openAmount}</td>
                      <td className="px-3 py-2">{row.paymentStatus}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </IndustrialPanel>

        <IndustrialPanel title="账目时间线">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-xs">
              <thead>
                <tr className={tableHeaderRowClass}>
                  <th className="px-3 py-2">日期</th>
                  <th className="px-3 py-2">单号</th>
                  <th className="px-3 py-2">类型</th>
                  <th className="px-3 py-2">摘要</th>
                  <th className={`${moneyCellClass} !px-3`}>金额</th>
                  <th className={`${moneyCellClass} !px-3`}>未收</th>
                  <th className="px-3 py-2">支付状态</th>
                </tr>
              </thead>
              <tbody>
                {timelineRows.length === 0 ? (
                  <tr className={tableBodyRowClass}>
                    <td colSpan={7} className="px-3 py-6 text-center text-[var(--color-text-muted)]">
                      {detailQuery.isLoading ? "加载中…" : "暂无账目记录"}
                    </td>
                  </tr>
                ) : (
                  timelineRows.map((row) => (
                    <tr key={row.id} className={tableBodyRowClass}>
                      <td className="px-3 py-2">{row.occurredOn}</td>
                      <td className="px-3 py-2 font-mono text-[11px]">{row.entryNo}</td>
                      <td className="px-3 py-2">{row.sourceLabel}</td>
                      <td className="px-3 py-2">
                        <div>{row.title}</div>
                        {row.allocations.length > 0 ? (
                          <div className="mt-1 text-[10px] text-[var(--color-text-muted)]">
                            核销：{row.allocations.map((a) => `${a.receivable_entry_no ?? ""} ${money(a.amount)}`).join("；")}
                          </div>
                        ) : null}
                      </td>
                      <td className={`${moneyCellClass} !px-3`}>{row.amount}</td>
                      <td className={`${moneyCellClass} !px-3`}>{row.entryKind === "receivable" ? row.openAmount : "—"}</td>
                      <td className="px-3 py-2">{row.paymentStatus}</td>
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

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="财务中心 · 客户应收"
        subtitle="按客户汇总应收、已收与欠款；可手动添加客户并录入账单"
        actions={
          canCreate ? (
            <WorkspaceToolbarButton
              variant="primary"
              onClick={() => { setShowAddCustomer((v) => !v); setFormError(null); }}
            >
              {showAddCustomer ? "取消添加" : "添加客户"}
            </WorkspaceToolbarButton>
          ) : null
        }
      />
      <FinanceSubNav />

      {showAddCustomer && canCreate ? (
        <IndustrialPanel title="添加客户账目">
          <div className={`${formPanelClass} flex flex-wrap items-end gap-3`}>
            <label className="block min-w-[240px] flex-1 space-y-1 text-xs">
              <span className={fieldLabelClass}>选择客户 *</span>
              <select
                className={fieldInputClass}
                value={addCustomerId}
                onChange={(e) => setAddCustomerId(e.target.value)}
              >
                <option value="">请选择客户</option>
                {addableCustomers.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <WorkspaceToolbarButton
              variant="primary"
              onClick={() => void handleAddCustomer()}
              disabled={registerMutation.isPending}
              loading={registerMutation.isPending}
            >
              确认添加
            </WorkspaceToolbarButton>
          </div>
          {addableCustomers.length === 0 ? (
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">暂无可添加客户（已在明细中或客户库为空）</p>
          ) : null}
          {formError ? <p className="mt-3 text-xs text-[var(--color-danger)]">{formError}</p> : null}
        </IndustrialPanel>
      ) : null}

      <IndustrialPanel>
        <FilterBar>
          <label className={`${filterFieldClass} min-w-[220px] flex-1`}>
            <span className={fieldLabelClass}>客户搜索</span>
            <input
              className={fieldInputClass}
              placeholder="名称或编码"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label className={filterCheckClass}>
            <input
              type="checkbox"
              checked={outstandingOnly}
              onChange={(e) => {
                setOutstandingOnly(e.target.checked);
                setPage(1);
              }}
            />
            仅显示有欠款客户
          </label>
        </FilterBar>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-3 py-2">客户</th>
                <th className="px-3 py-2">编码</th>
                <th className={`${moneyCellClass} !px-3`}>应收合计</th>
                <th className={`${moneyCellClass} !px-3`}>已收合计</th>
                <th className={`${moneyCellClass} !px-3`}>欠款</th>
                <th className={`${moneyCellClass} !px-3`}>未结清</th>
                <th className="px-3 py-2">最近业务日</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {customerRows.length === 0 ? (
                <tr className={tableBodyRowClass}>
                  <td colSpan={8} className="px-3 py-6 text-center text-[var(--color-text-muted)]">
                    {customersQuery.isLoading ? "加载中…" : "暂无客户账目，请先添加客户"}
                  </td>
                </tr>
              ) : (
                customerRows.map((row) => (
                  <tr key={row.id} className={tableBodyRowClass}>
                    <td className="px-3 py-2">{row.name}</td>
                    <td className="px-3 py-2 font-mono text-[11px]">{row.code || "—"}</td>
                    <td className={`${moneyCellClass} !px-3`}>{row.receivableTotal}</td>
                    <td className={`${moneyCellClass} !px-3`}>{row.receivedTotal}</td>
                    <td className={`${moneyCellClass} !px-3 text-[var(--color-warning)]`}>{row.outstandingTotal}</td>
                    <td className={`${moneyCellClass} !px-3`}>{row.openBillCount}</td>
                    <td className="px-3 py-2">{row.lastDate}</td>
                    <td className="px-3 py-2">
                      <button type="button" className={linkActionClass} onClick={() => openDetail(row.id, row.name)}>
                        查看明细
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {customerTotal > 20 ? (
          <div className="mt-4 flex items-center gap-2 text-xs">
            <WorkspaceToolbarButton disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              上一页
            </WorkspaceToolbarButton>
            <span className="text-[var(--color-text-muted)]">
              第 {page} 页 · 共 {customerTotal} 条
            </span>
            <WorkspaceToolbarButton
              disabled={page * 20 >= customerTotal}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </WorkspaceToolbarButton>
          </div>
        ) : null}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
