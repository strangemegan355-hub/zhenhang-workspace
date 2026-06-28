"use client";

import {
  useBusinessSettingsQuery,
  useUpdateBusinessSettingsMutation,
  type BusinessSettings,
} from "@zhenhang/query-hooks";
import {
  ErrorBanner,
  IndustrialPage,
  IndustrialPanel,
  PanelSkeleton,
  WorkspaceToolbarButton,
  typography,
} from "@zhenhang/ui";
import { useState } from "react";
import {
  fieldInputClass,
  fieldLabelClass,
  fieldTextareaClass,
  sectionDividerClass,
} from "@/lib/form-styles";

function mapBusinessSettings(data: BusinessSettings): BusinessSettings {
  return {
    company_name: data.company_name ?? "",
    company_phone: data.company_phone ?? "",
    company_address: data.company_address ?? "",
    company_email: data.company_email ?? "",
    export_footer: data.export_footer ?? "",
    company_remark: data.company_remark ?? "",
    default_currency: data.default_currency ?? "CNY",
    default_scrap_rate: Number(data.default_scrap_rate ?? 0),
    default_overhead_rate: Number(data.default_overhead_rate ?? 0),
    default_profit_rate: Number(data.default_profit_rate ?? 20),
    default_tax_rate: Number(data.default_tax_rate ?? 13),
    accounting_enabled: Boolean(data.accounting_enabled ?? false),
    quote_receivable_enabled: Boolean(data.quote_receivable_enabled ?? false),
    procurement_approval_enabled: Boolean(data.procurement_approval_enabled ?? false),
    sales_max_discount_rate_pct: Number(data.sales_max_discount_rate_pct ?? 0),
  };
}

function BusinessSettingsEditor({
  initial,
  saving,
  onSave,
}: {
  initial: BusinessSettings;
  saving: boolean;
  onSave: (body: BusinessSettings) => Promise<BusinessSettings>;
}) {
  const [form, setForm] = useState(initial);
  const [formError, setFormError] = useState<string | null>(null);
  const [savedHint, setSavedHint] = useState<string | null>(null);

  const handleSave = async () => {
    setFormError(null);
    setSavedHint(null);
    if (!form.company_name.trim()) {
      setFormError("请填写公司名称");
      return;
    }
    try {
      const saved = await onSave({
        company_name: form.company_name.trim(),
        company_phone: form.company_phone?.trim() || undefined,
        company_address: form.company_address?.trim() || undefined,
        company_email: form.company_email?.trim() || undefined,
        company_remark: form.company_remark?.trim() || undefined,
        export_footer: form.export_footer?.trim() || undefined,
        default_currency: form.default_currency,
        default_scrap_rate: form.default_scrap_rate,
        default_overhead_rate: form.default_overhead_rate,
        default_profit_rate: form.default_profit_rate,
        default_tax_rate: form.default_tax_rate,
        accounting_enabled: Boolean(form.accounting_enabled),
        quote_receivable_enabled: Boolean(form.quote_receivable_enabled),
        procurement_approval_enabled: Boolean(form.procurement_approval_enabled),
        sales_max_discount_rate_pct: Number(form.sales_max_discount_rate_pct ?? 0),
      });
      setForm(mapBusinessSettings(saved));
      setSavedHint(
        saved.accounting_enabled
          ? "已保存，记账功能已开启，请刷新页面或稍候侧栏将出现「财务中心」"
          : "已保存，报价导出将使用最新公司抬头与默认参数",
      );
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "保存失败");
    }
  };

  return (
    <>
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <section className="space-y-3">
          <h3 className={typography.sectionTitle}>公司资料</h3>
          <p className={typography.caption}>用于报价导出抬头、页脚及系统展示，对齐旧版「系统设置」公司区块。</p>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>公司名称 *</span>
              <input
                className={fieldInputClass}
                value={form.company_name}
                onChange={(e) => setForm((s) => ({ ...s, company_name: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>公司电话</span>
              <input
                className={fieldInputClass}
                value={form.company_phone ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, company_phone: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>公司邮箱</span>
              <input
                className={fieldInputClass}
                value={form.company_email ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, company_email: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>公司地址</span>
              <input
                className={fieldInputClass}
                value={form.company_address ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, company_address: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>公司简介 / 抬头备注</span>
              <textarea
                className={fieldTextareaClass}
                value={form.company_remark ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, company_remark: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>报价导出页脚</span>
              <textarea
                className={fieldTextareaClass}
                value={form.export_footer ?? ""}
                onChange={(e) => setForm((s) => ({ ...s, export_footer: e.target.value }))}
              />
            </label>
          </div>
        </section>

        <section className={`space-y-3 ${sectionDividerClass}`}>
          <h3 className={typography.sectionTitle}>默认报价参数</h3>
          <p className={typography.caption}>新建报价时可作为默认值；税率、币种将写入导出上下文。</p>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>默认币种</span>
              <select
                className={fieldInputClass}
                value={form.default_currency}
                onChange={(e) => setForm((s) => ({ ...s, default_currency: e.target.value }))}
              >
                <option value="CNY">CNY 人民币</option>
                <option value="USD">USD 美元</option>
                <option value="EUR">EUR 欧元</option>
              </select>
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>默认损耗率 (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                className={fieldInputClass}
                value={form.default_scrap_rate}
                onChange={(e) => setForm((s) => ({ ...s, default_scrap_rate: Number(e.target.value) }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>默认管理费率 (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                className={fieldInputClass}
                value={form.default_overhead_rate}
                onChange={(e) => setForm((s) => ({ ...s, default_overhead_rate: Number(e.target.value) }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>默认利润率 (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.1}
                className={fieldInputClass}
                value={form.default_profit_rate}
                onChange={(e) => setForm((s) => ({ ...s, default_profit_rate: Number(e.target.value) }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>默认税率 (%)</span>
              <input
                type="number"
                min={0}
                max={100}
                step={0.01}
                className={fieldInputClass}
                value={form.default_tax_rate}
                onChange={(e) => setForm((s) => ({ ...s, default_tax_rate: Number(e.target.value) }))}
              />
            </label>
          </div>
        </section>

        <section className={`space-y-3 ${sectionDividerClass}`}>
          <h3 className={typography.sectionTitle}>记账功能开关</h3>
          <p className={typography.caption}>
            默认全部关闭，不影响现有业务。关闭时侧栏隐藏对应菜单，API 返回 403。可随时回滚。
          </p>
          <div className="grid gap-3 md:grid-cols-1">
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={Boolean(form.accounting_enabled)}
                onChange={(e) => setForm((s) => ({ ...s, accounting_enabled: e.target.checked }))}
              />
              <span>开启记账功能（收支台账 / 补录账，P1 起可用）</span>
            </label>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={Boolean(form.quote_receivable_enabled)}
                onChange={(e) => setForm((s) => ({ ...s, quote_receivable_enabled: e.target.checked }))}
                disabled={!form.accounting_enabled}
              />
              <span>开启对客报价生成应收（P2，需先开启记账）</span>
            </label>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={Boolean(form.procurement_approval_enabled)}
                onChange={(e) => setForm((s) => ({ ...s, procurement_approval_enabled: e.target.checked }))}
                disabled={!form.accounting_enabled}
              />
              <span>开启采购老板审批与应付（P3，需先开启记账）</span>
            </label>
          </div>
        </section>

        <section className={`space-y-3 ${sectionDividerClass}`}>
          <h3 className={typography.sectionTitle}>销售优惠策略</h3>
          <p className={typography.caption}>
            设置销售可自主让利的上限。整单优惠率不超过此值时，销售申请应收后可直接确认；超过此值须进入审批中心由老板审批。
          </p>
          <label className="block max-w-xs space-y-1 text-xs">
            <span className={fieldLabelClass}>销售免审优惠上限 (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              step={0.1}
              className={fieldInputClass}
              value={form.sales_max_discount_rate_pct ?? 0}
              onChange={(e) => setForm((s) => ({ ...s, sales_max_discount_rate_pct: Number(e.target.value) }))}
              disabled={!form.quote_receivable_enabled}
            />
          </label>
          <p className="text-xs text-[var(--color-text-muted)]">
            设为 0 表示任何优惠都需老板审批；设为 5 表示优惠率 ≤5% 时销售可自主确认应收。
          </p>
        </section>

        {formError ? <p className="text-xs text-red-500">{formError}</p> : null}
        {savedHint ? <p className="text-xs text-emerald-600">{savedHint}</p> : null}
      </div>
      <div className="mt-4 flex justify-end">
        <WorkspaceToolbarButton loading={saving} onClick={() => void handleSave()}>
          保存设置
        </WorkspaceToolbarButton>
      </div>
    </>
  );
}

export default function BusinessSettingsPage() {
  const query = useBusinessSettingsQuery();
  const saveMutation = useUpdateBusinessSettingsMutation();

  return (
    <IndustrialPage gap="md" fill>
      <IndustrialPanel
        fill
        title="业务设置"
        inlineLoading={query.isFetching && !query.isLoading}
      >
        {query.isLoading ? (
          <PanelSkeleton />
        ) : query.isError ? (
          <ErrorBanner message="无法加载业务设置。" onRetry={() => query.refetch()} />
        ) : query.data ? (
          <BusinessSettingsEditor
            initial={mapBusinessSettings(query.data)}
            saving={saveMutation.isPending}
            onSave={async (body) => {
              const saved = await saveMutation.mutateAsync(body);
              return mapBusinessSettings(saved);
            }}
          />
        ) : null}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
