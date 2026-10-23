"use client";

import { BomTreeEditor, flatBomToTree, type BomTreeNode } from "@zhenhang/quote-builder";
import { StatusBadge, workflowStateToStatus, typography } from "@zhenhang/ui";
import { Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";

export type QuoteListItem = {
  id: string;
  quoteNo: string;
  title: string;
  amount: number;
  status: string;
};

export type MasterOption = { id: string; label: string; sub?: string };

export type CreateQuoteForm = {
  title: string;
  customerId: string;
  productId: string;
  costTemplateId: string;
  priceTemplateId: string;
  machineId: string;
  bomId: string;
  approvalTemplateId: string;
  currency: string;
  remark: string;
  seedFromProduct: boolean;
  seedFromBom: boolean;
};

type QuoteProductPanelProps = {
  quotes: QuoteListItem[];
  activeQuoteId: string | null;
  onSelectQuote: (id: string) => void;
  createMode: boolean;
  onCreateModeChange: (open: boolean) => void;
  createForm: CreateQuoteForm;
  onCreateFormChange: (form: CreateQuoteForm) => void;
  onCreateSubmit: () => void;
  creating?: boolean;
  createError?: string;
  customers: MasterOption[];
  products: MasterOption[];
  costTemplates: MasterOption[];
  priceTemplates: MasterOption[];
  machines: MasterOption[];
  boms: MasterOption[];
  approvalTemplates: MasterOption[];
  productName?: string;
  onImportProduct?: () => void;
  bomNodes: BomTreeNode[];
  bomLoading?: boolean;
  quoteNo?: string;
  onImportBom?: () => void;
  readOnly?: boolean;
  loading?: boolean;
};

const STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
  rejected: "已驳回",
};

const inputClass =
  "mt-1 h-8 w-full rounded border border-[var(--color-border)] bg-white px-2 text-xs text-[var(--color-text)] focus:border-[var(--color-primary)] focus:outline-none";

export function QuoteProductPanel({
  quotes,
  activeQuoteId,
  onSelectQuote,
  createMode,
  onCreateModeChange,
  createForm,
  onCreateFormChange,
  onCreateSubmit,
  creating,
  createError,
  customers,
  products,
  costTemplates,
  priceTemplates,
  machines,
  boms,
  approvalTemplates,
  bomNodes,
  bomLoading,
  quoteNo,
  productName,
  onImportBom,
  onImportProduct,
  readOnly,
  loading,
}: QuoteProductPanelProps) {
  const [search, setSearch] = useState("");
  /** UX-001: 机型/BOM 默认折叠，标准路径只选产品库 */
  const [showAdvancedMachine, setShowAdvancedMachine] = useState(false);
  const filteredCostTemplates = useMemo(
    () =>
      createForm.productId
        ? costTemplates.filter((t) => !t.sub || t.sub.includes(createForm.productId))
        : costTemplates,
    [costTemplates, createForm.productId],
  );
  const filteredPriceTemplates = useMemo(
    () =>
      createForm.productId
        ? priceTemplates.filter((t) => !t.sub || t.sub.includes(createForm.productId))
        : priceTemplates,
    [priceTemplates, createForm.productId],
  );
  const filteredBoms = useMemo(
    () => (createForm.machineId ? boms.filter((b) => b.sub?.includes(createForm.machineId)) : boms),
    [boms, createForm.machineId],
  );
  const filteredQuotes = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return quotes;
    return quotes.filter(
      (r) => r.quoteNo.toLowerCase().includes(q) || r.title.toLowerCase().includes(q),
    );
  }, [quotes, search]);

  const patch = (partial: Partial<CreateQuoteForm>) => onCreateFormChange({ ...createForm, ...partial });

  return (
    <aside className="flex h-full min-h-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-soft)]">
      <div className="border-b border-[var(--color-border)] p-3">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h2 className={`${typography.cardTitle} text-sm`}>产品选择</h2>
          <button
            type="button"
            onClick={() => onCreateModeChange(true)}
            className="inline-flex h-7 items-center gap-1 rounded-lg bg-[var(--color-primary)] px-2.5 text-[11px] font-medium text-white hover:bg-[var(--color-primary-hover)]"
          >
            <Plus className="h-3.5 w-3.5" />
            新建
          </button>
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--color-text-muted)]" />
          <input
            className="h-8 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] pl-8 pr-2 text-xs text-[var(--color-text)]"
            placeholder="搜索报价单…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="max-h-[200px] shrink-0 overflow-auto border-b border-[var(--color-border)]">
        {loading ? (
          <p className="p-3 text-xs text-[var(--color-text-muted)]">加载报价列表…</p>
        ) : filteredQuotes.length === 0 ? (
          <p className="p-3 text-xs text-[var(--color-text-muted)]">暂无报价，点击「新建」创建</p>
        ) : (
          <ul className="p-1">
            {filteredQuotes.map((row) => {
              const active = row.id === activeQuoteId && !createMode;
              return (
                <li key={row.id}>
                  <button
                    type="button"
                    onClick={() => {
                      onCreateModeChange(false);
                      onSelectQuote(row.id);
                    }}
                    className={`w-full rounded-lg px-2.5 py-2 text-left transition ${
                      active ? "bg-[var(--color-primary-soft)] ring-1 ring-[var(--color-primary)]/20" : "hover:bg-white/80 dark:hover:bg-[#1e293b]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-xs font-semibold text-[var(--color-text)] dark:text-[#f1f5f9]">
                        {row.quoteNo}
                      </span>
                      <StatusBadge
                        status={workflowStateToStatus(row.status)}
                        label={STATUS_LABEL[row.status] ?? row.status}
                        compact
                      />
                    </div>
                    <p className="mt-0.5 truncate text-[11px] text-[var(--color-text-muted)]">{row.title}</p>
                    <p className="mt-0.5 text-right text-[11px] font-medium tabular-nums text-[var(--color-text)]">
                      ¥{row.amount.toLocaleString("zh-CN")}
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-3">
        {createMode ? (
          <div className="space-y-3">
            <p className="text-xs font-medium text-[var(--color-text)] dark:text-[#f1f5f9]">新建报价 · 产品信息</p>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              报价标题 *
              <input className={inputClass} value={createForm.title} onChange={(e) => patch({ title: e.target.value })} placeholder="XX 产线改造报价" />
            </label>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              客户 *
              <select className={inputClass} value={createForm.customerId} onChange={(e) => patch({ customerId: e.target.value })}>
                <option value="">请选择</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              产品 *
              <select
                className={inputClass}
                value={createForm.productId}
                onChange={(e) =>
                  patch({
                    productId: e.target.value,
                    costTemplateId: "",
                    priceTemplateId: "",
                    machineId: "",
                    bomId: "",
                  })
                }
              >
                <option value="">请选择</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              成本模板
              <select
                className={inputClass}
                value={createForm.costTemplateId}
                onChange={(e) => patch({ costTemplateId: e.target.value })}
                disabled={!createForm.productId}
              >
                <option value="">产品默认</option>
                {filteredCostTemplates.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              售价模板
              <select
                className={inputClass}
                value={createForm.priceTemplateId}
                onChange={(e) => patch({ priceTemplateId: e.target.value })}
                disabled={!createForm.productId}
              >
                <option value="">产品默认</option>
                {filteredPriceTemplates.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
              <input type="checkbox" checked={createForm.seedFromProduct} onChange={(e) => patch({ seedFromProduct: e.target.checked })} />
              从产品模板生成首版行项目
            </label>
            <label className="block text-[11px] text-[var(--color-text-muted)]">
              审批模板
              <select className={inputClass} value={createForm.approvalTemplateId} onChange={(e) => patch({ approvalTemplateId: e.target.value })}>
                <option value="">默认</option>
                {approvalTemplates.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </label>
            <div className="rounded border border-dashed border-[var(--color-border)] p-2">
              <button
                type="button"
                className="w-full text-left text-[11px] font-medium text-[var(--color-primary)] hover:underline"
                onClick={() => setShowAdvancedMachine((v) => !v)}
              >
                {showAdvancedMachine ? "收起" : "展开"}高级：机型 / BOM（旧路径，一般不需要）
              </button>
              {showAdvancedMachine ? (
                <div className="mt-2 space-y-2">
                  <label className="block text-[11px] text-[var(--color-text-muted)]">
                    机型
                    <select
                      className={inputClass}
                      value={createForm.machineId}
                      onChange={(e) => patch({ machineId: e.target.value, bomId: "" })}
                    >
                      <option value="">不绑定</option>
                      {machines.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-[11px] text-[var(--color-text-muted)]">
                    BOM
                    <select
                      className={inputClass}
                      value={createForm.bomId}
                      onChange={(e) => patch({ bomId: e.target.value })}
                      disabled={!createForm.machineId}
                    >
                      <option value="">不绑定 / 稍后导入</option>
                      {filteredBoms.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
                    <input
                      type="checkbox"
                      checked={createForm.seedFromBom}
                      onChange={(e) => patch({ seedFromBom: e.target.checked })}
                      disabled={!createForm.bomId}
                    />
                    从 BOM 生成首版行项目
                  </label>
                </div>
              ) : null}
            </div>
            {createError ? <p className="text-[11px] text-red-500">{createError}</p> : null}
            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  creating ||
                  !createForm.title.trim() ||
                  !createForm.customerId ||
                  // K-005: product_id required; machine/BOM advanced is optional only
                  !createForm.productId
                }
                onClick={onCreateSubmit}
                className="flex-1 rounded-lg bg-[var(--color-primary)] py-2 text-xs font-medium text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
              >
                {creating ? "创建中…" : "创建报价"}
              </button>
              <button
                type="button"
                onClick={() => onCreateModeChange(false)}
                className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)]"
              >
                取消
              </button>
            </div>
          </div>
        ) : activeQuoteId ? (
          <div className="space-y-3">
            {productName ? (
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
                <p className="text-[11px] text-[var(--color-text-muted)]">关联产品</p>
                <p className="text-xs font-medium text-[var(--color-text)] dark:text-[#f1f5f9]">{productName}</p>
                {onImportProduct ? (
                  <button
                    type="button"
                    onClick={onImportProduct}
                    className="mt-2 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-primary-soft)] py-1.5 text-[11px] font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-soft)]"
                  >
                    从产品模板导入明细
                  </button>
                ) : null}
              </div>
            ) : null}
            <p className="text-xs font-medium text-[var(--color-text)] dark:text-[#f1f5f9]">当前产品 BOM</p>
            <BomTreeEditor
              nodes={bomNodes}
              rootLabel={quoteNo ? `BOM · ${quoteNo}` : "设备 BOM"}
              onImportToQuote={readOnly ? undefined : onImportBom}
              readOnly={readOnly}
              embedded
              loading={bomLoading}
            />
          </div>
        ) : (
          <p className="text-xs text-[var(--color-text-muted)]">请选择报价单，或点击「新建」开始</p>
        )}
      </div>
    </aside>
  );
}

export function mapBomItemsToNodes(
  items: Array<{ id: string; item_code: string; item_name: string; quantity: number; unit_cost: number; line_total?: number }>,
): BomTreeNode[] {
  return items.length ? flatBomToTree(items, true) : [];
}
