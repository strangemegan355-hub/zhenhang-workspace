"use client";

import { MasterListPage } from "@/components/master/master-list-page";
import {
  useAccountingStatusQuery,
  useBusinessSettingsQuery,
  useConfirmQuoteReceivableMutation,
  useCreateCustomerQuoteMutation,
  useCreateQuoteReceivableRequestMutation,
  useCustomersQuery,
  useDeleteCustomerQuoteMutation,
  useProductCategoriesQuery,
  useProductsQuery,
  useProjectsQuery,
  useQuoteDetailQuery,
  useQuoteReceivableRequestQuery,
  useQuotesQuery,
  useUpdateCustomerQuoteMutation,
  type CustomerQuoteLine,
  type CustomerQuotePayload,
} from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, WorkspaceToolbarButton, typography } from "@zhenhang/ui";
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
import { isMotorCategory } from "@/lib/product-category-labels";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";

type ListRow = {
  id: string;
  quoteNo: string;
  title: string;
  finalTotal: string;
  status: string;
  receivableStatus: string;
};

type ProductCatalogItem = {
  id: string;
  name: string;
  spec: string;
  unit: string;
  reference_price: number;
  category_id: string;
  is_motor: boolean;
};

const emptyLine = (): CustomerQuoteLine => ({
  name: "",
  spec: "",
  unit: "",
  power_kw: "",
  motor_product_id: undefined,
  motor_unit_price: 0,
  quantity: 1,
  unit_price: 0,
});

function money(n: number) {
  return n.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function lineAmount(line: CustomerQuoteLine): number {
  const qty = line.quantity || 0;
  return qty * ((line.unit_price || 0) + (line.motor_unit_price || 0));
}

function lineReferenceAmount(
  line: CustomerQuoteLine,
  mainCatalog: ProductCatalogItem[],
  motorCatalog: ProductCatalogItem[],
): number {
  const qty = line.quantity || 0;
  const product = mainCatalog.find((p) => p.id === line.product_id);
  const motor = motorCatalog.find((p) => p.id === line.motor_product_id);
  const refUnit = product?.reference_price ?? line.unit_price ?? 0;
  const refMotor = motor?.reference_price ?? line.motor_unit_price ?? 0;
  return qty * (refUnit + refMotor);
}

function lineDiscount(
  line: CustomerQuoteLine,
  mainCatalog: ProductCatalogItem[],
  motorCatalog: ProductCatalogItem[],
): number {
  return Math.max(0, lineReferenceAmount(line, mainCatalog, motorCatalog) - lineAmount(line));
}

function applyProductVariant(line: CustomerQuoteLine, product: ProductCatalogItem): CustomerQuoteLine {
  return {
    ...line,
    product_id: product.id,
    machine_id: undefined,
    name: product.name,
    spec: product.spec,
    unit: product.unit,
    unit_price: product.reference_price,
    power_kw: product.is_motor ? product.spec : line.power_kw,
  };
}

function detailToCustomerQuoteForm(
  d: Record<string, unknown>,
  defaultTaxRate: number,
): {
  title: string;
  customerId: string;
  projectId: string;
  taxRate: number;
  remark: string;
  lines: CustomerQuoteLine[];
} {
  const items = (d.items as Record<string, unknown>[]) ?? [];
  const machItems = items
    .filter((item) => String(item.item_code ?? "").startsWith("MACH-"))
    .sort((a, b) => String(a.item_code).localeCompare(String(b.item_code), undefined, { numeric: true }));
  const motorByIdx = new Map<number, Record<string, unknown>>();
  items
    .filter((item) => String(item.item_code ?? "").startsWith("MOTOR-"))
    .forEach((item) => {
      const match = String(item.item_code ?? "").match(/MOTOR-(\d+)/);
      if (match) motorByIdx.set(Number(match[1]) - 1, item);
    });

  return {
    title: String(d.title ?? ""),
    customerId: String(d.customer_id ?? ""),
    projectId: d.project_id ? String(d.project_id) : "",
    taxRate: Number(d.tax_rate ?? defaultTaxRate),
    remark: String(d.remark ?? ""),
    lines: machItems.length
      ? machItems.map((item, idx) => {
          const motor = motorByIdx.get(idx);
          return {
            product_id: item.product_id ? String(item.product_id) : undefined,
            machine_id: item.machine_id ? String(item.machine_id) : undefined,
            name: String(item.item_name ?? ""),
            spec: String(item.spec ?? ""),
            unit: String(item.unit ?? ""),
            power_kw: motor ? String(motor.power_kw ?? motor.spec ?? "") : String(item.power_kw ?? ""),
            motor_product_id: motor?.product_id ? String(motor.product_id) : undefined,
            motor_unit_price: motor ? Number(motor.unit_price ?? 0) : 0,
            quantity: Number(item.quantity ?? 1),
            unit_price: Number(item.unit_price ?? 0),
          };
        })
      : [emptyLine()],
  };
}

const RECEIVABLE_LABEL: Record<string, string> = {
  none: "未申请",
  pending: "优惠待批",
  approved: "待确认应收",
  posted: "已生成应收",
};

export default function CustomerQuotePage() {
  const user = useAuthStore((s) => s.user);
  const perms = user?.permissions ?? [];
  const canPostQuote = hasPermission(perms, "business:accounting:post_quote");
  const canConfirmReceivable = hasPermission(perms, "business:accounting:confirm_receivable");

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<"list" | "edit">("list");
  const [editId, setEditId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [taxRate, setTaxRate] = useState(13);
  const [remark, setRemark] = useState("");
  const [lines, setLines] = useState<CustomerQuoteLine[]>([emptyLine()]);
  const [formError, setFormError] = useState<string | null>(null);
  const [formHydrationKey, setFormHydrationKey] = useState("list");

  const listQuery = useQuotesQuery({ page, keyword: search.trim() || undefined, quoteKind: "customer" });
  const detailQuery = useQuoteDetailQuery(editId);
  const customersQuery = useCustomersQuery(1);
  const productsQuery = useProductsQuery(1);
  const categoriesQuery = useProductCategoriesQuery(1);
  const projectsQuery = useProjectsQuery(1);
  const settingsQuery = useBusinessSettingsQuery();
  const accountingStatusQuery = useAccountingStatusQuery();
  const createMutation = useCreateCustomerQuoteMutation();
  const updateMutation = useUpdateCustomerQuoteMutation();
  const deleteMutation = useDeleteCustomerQuoteMutation();
  const receivableRequestQuery = useQuoteReceivableRequestQuery(editId, mode === "edit" && Boolean(editId));
  const createReceivableMutation = useCreateQuoteReceivableRequestMutation();
  const confirmReceivableMutation = useConfirmQuoteReceivableMutation();
  const [receivableError, setReceivableError] = useState<string | null>(null);

  const quoteReceivableEnabled =
    (accountingStatusQuery.data?.flags.accounting_enabled ?? false) &&
    (accountingStatusQuery.data?.flags.quote_receivable_enabled ?? false);

  const listData = (listQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const motorCategoryIds = useMemo(() => {
    const items = (categoriesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];
    return new Set(
      items.filter((c) => isMotorCategory(String(c.name ?? ""))).map((c) => String(c.id ?? "")),
    );
  }, [categoriesQuery.data]);

  const customerOptions = useMemo(() => {
    const items = (customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];
    return items.map((c) => ({
      value: String(c.id ?? ""),
      label: String(c.name ?? ""),
      code: String(c.code ?? ""),
    }));
  }, [customersQuery.data]);

  const productCatalog = useMemo<ProductCatalogItem[]>(
    () =>
      ((productsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => {
        const categoryId = String(p.category_id ?? "");
        return {
          id: String(p.id ?? ""),
          name: String(p.name ?? ""),
          spec: String(p.spec ?? ""),
          unit: String(p.unit ?? "\u53f0"),
          reference_price: Number(p.reference_price ?? 0),
          category_id: categoryId,
          is_motor: motorCategoryIds.has(categoryId),
        };
      }),
    [productsQuery.data, motorCategoryIds],
  );

  const mainProductCatalog = useMemo(() => productCatalog.filter((p) => !p.is_motor), [productCatalog]);
  const motorCatalog = useMemo(() => productCatalog.filter((p) => p.is_motor), [productCatalog]);

  const productModelOptions = useMemo(
    () =>
      [...new Set(mainProductCatalog.map((p) => p.name).filter(Boolean))].sort((a, b) =>
        a.localeCompare(b, "zh-CN"),
      ),
    [mainProductCatalog],
  );

  const projectOptions = useMemo(
    () =>
      ((projectsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((p) => ({
        value: String(p.id ?? ""),
        label: `${String(p.project_no ?? "")} · ${String(p.name ?? "")}`,
      })),
    [projectsQuery.data],
  );

  const rows = useMemo(
    () =>
      (listData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        quoteNo: String(row.quote_no ?? ""),
        title: String(row.title ?? ""),
        finalTotal: money(Number(row.total_amount ?? 0)),
        status: String(row.workflow_state ?? "draft") === "draft" ? "草稿" : String(row.workflow_state ?? ""),
        receivableStatus: RECEIVABLE_LABEL[String(row.receivable_status ?? "none")] ?? String(row.receivable_status ?? ""),
      })),
    [listData.items],
  );

  const subtotal = useMemo(() => lines.reduce((sum, line) => sum + lineAmount(line), 0), [lines]);
  const standardSubtotal = useMemo(
    () => lines.reduce((sum, line) => sum + lineReferenceAmount(line, mainProductCatalog, motorCatalog), 0),
    [lines, mainProductCatalog, motorCatalog],
  );
  const taxAmount = useMemo(() => (subtotal * taxRate) / 100, [subtotal, taxRate]);
  const standardTaxAmount = useMemo(() => (standardSubtotal * taxRate) / 100, [standardSubtotal, taxRate]);
  const finalTotal = useMemo(() => subtotal + taxAmount, [subtotal, taxAmount]);
  const standardFinalTotal = useMemo(() => standardSubtotal + standardTaxAmount, [standardSubtotal, standardTaxAmount]);
  const discountFinalTotal = useMemo(
    () => Math.max(0, standardFinalTotal - finalTotal),
    [standardFinalTotal, finalTotal],
  );
  const salesMaxDiscountPct = Number(settingsQuery.data?.sales_max_discount_rate_pct ?? 0);
  const discountRatePct = useMemo(
    () => (standardFinalTotal > 0 ? (discountFinalTotal / standardFinalTotal) * 100 : 0),
    [discountFinalTotal, standardFinalTotal],
  );
  const needsBossForDiscount = discountFinalTotal > 0 && discountRatePct > salesMaxDiscountPct;

  const targetHydrationKey =
    mode === "edit"
      ? editId
        ? detailQuery.data
          ? `edit:${editId}:${detailQuery.dataUpdatedAt}`
          : "edit:pending"
        : "create"
      : "list";

  if (
    targetHydrationKey !== "list" &&
    targetHydrationKey !== "edit:pending" &&
    targetHydrationKey !== formHydrationKey
  ) {
    setFormHydrationKey(targetHydrationKey);
    if (targetHydrationKey === "create") {
      setTitle("");
      setCustomerId(customerOptions.find((c) => c.code === "WALK-IN")?.value ?? "");
      setProjectId("");
      setTaxRate(Number(settingsQuery.data?.default_tax_rate ?? 13));
      setRemark("");
      setLines([emptyLine()]);
    } else if (detailQuery.data) {
      const mapped = detailToCustomerQuoteForm(
        detailQuery.data as Record<string, unknown>,
        Number(settingsQuery.data?.default_tax_rate ?? 13),
      );
      setTitle(mapped.title);
      setCustomerId(mapped.customerId);
      setProjectId(mapped.projectId);
      setTaxRate(mapped.taxRate);
      setRemark(mapped.remark);
      setLines(mapped.lines);
    }
  }

  const openCreate = () => {
    setEditId(null);
    setTitle("");
    setCustomerId(customerOptions.find((c) => c.code === "WALK-IN")?.value ?? "");
    setProjectId("");
    setTaxRate(Number(settingsQuery.data?.default_tax_rate ?? 13));
    setRemark("");
    setLines([emptyLine()]);
    setFormError(null);
    setMode("edit");
  };

  const openEdit = (id: string) => {
    setEditId(id);
    setFormError(null);
    setMode("edit");
  };

  const backToList = () => {
    setMode("list");
    setEditId(null);
    setFormHydrationKey("list");
    void listQuery.refetch();
  };

  const pickProductName = (index: number, modelName: string) => {
    const variants = mainProductCatalog.filter((p) => p.name === modelName);
    setLines((prev) => {
      const next = [...prev];
      let line: CustomerQuoteLine = {
        ...next[index],
        name: modelName,
        product_id: undefined,
        machine_id: undefined,
        spec: "",
        unit: "",
        unit_price: 0,
      };
      if (variants.length === 1) {
        line = applyProductVariant(line, variants[0]!);
      }
      next[index] = line;
      return next;
    });
  };

  const pickProductSpec = (index: number, productId: string) => {
    const product = mainProductCatalog.find((p) => p.id === productId);
    if (!product) return;
    setLines((prev) => {
      const next = [...prev];
      next[index] = applyProductVariant(next[index], product);
      return next;
    });
  };

  const pickMotorPower = (index: number, motorProductId: string) => {
    const motor = motorCatalog.find((p) => p.id === motorProductId);
    setLines((prev) => {
      const next = [...prev];
      if (!motor) {
        next[index] = {
          ...next[index],
          motor_product_id: undefined,
          motor_unit_price: 0,
          power_kw: "",
        };
      } else {
        next[index] = {
          ...next[index],
          motor_product_id: motor.id,
          motor_unit_price: motor.reference_price,
          power_kw: motor.spec,
        };
      }
      return next;
    });
  };

  const updateLine = (index: number, patch: Partial<CustomerQuoteLine>) => {
    setLines((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  };

  const handleSave = async () => {
    setFormError(null);
    if (!title.trim()) {
      setFormError("请填写报价标题");
      return;
    }
    if (!customerId) {
      setFormError("请选择客户");
      return;
    }
    const validLines = lines.filter((l) => l.name.trim());
    if (!validLines.length) {
      setFormError("请至少添加一行有效产品明细");
      return;
    }
    const payload: CustomerQuotePayload = {
      title: title.trim(),
      customer_id: customerId,
      project_id: projectId || undefined,
      tax_rate: taxRate,
      remark: remark.trim() || undefined,
      machine_lines: validLines.map((l) => ({
        product_id: l.product_id,
        machine_id: l.machine_id,
        name: l.name.trim(),
        spec: l.spec?.trim() || undefined,
        unit: l.unit?.trim() || undefined,
        power_kw: l.power_kw?.trim() || undefined,
        motor_product_id: l.motor_product_id,
        motor_unit_price: l.motor_unit_price || 0,
        quantity: l.quantity || 1,
        unit_price: l.unit_price || 0,
      })),
    };
    try {
      if (editId) await updateMutation.mutateAsync({ id: editId, body: payload });
      else await createMutation.mutateAsync(payload);
      backToList();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const detailReceivableStatus = String((detailQuery.data as Record<string, unknown> | undefined)?.receivable_status ?? "none");
  const receivableRequest = receivableRequestQuery.data;

  const handleApplyReceivable = async () => {
    if (!editId) return;
    setReceivableError(null);
    try {
      await createReceivableMutation.mutateAsync(editId);
      void receivableRequestQuery.refetch();
      void detailQuery.refetch();
    } catch (err) {
      setReceivableError(err instanceof Error ? err.message : "申请失败");
    }
  };

  const handleConfirmReceivable = async () => {
    if (!receivableRequest?.id) return;
    setReceivableError(null);
    try {
      await confirmReceivableMutation.mutateAsync(receivableRequest.id);
      void receivableRequestQuery.refetch();
      void detailQuery.refetch();
    } catch (err) {
      setReceivableError(err instanceof Error ? err.message : "确认应收失败");
    }
  };

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`确定删除对客报价「{label}」吗？`.replace("{label}", label))) return;
    try {
      await deleteMutation.mutateAsync(id);
      void listQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  if (mode === "edit") {
    if (editId && !detailQuery.data) {
      return (
        <IndustrialPage gap="md" fill>
          <IndustrialPanel fill title="加载报价详情">
            <p className="text-sm text-[var(--color-text-muted)]">正在加载...</p>
          </IndustrialPanel>
        </IndustrialPage>
      );
    }

    return (
      <IndustrialPage gap="md" fill>
        <div className="flex items-center justify-between gap-2">
          <h2 className={typography.pageTitle}>{editId ? "编辑对客报价" : "新建对客报价"}</h2>
          <div className="flex gap-2">
            <WorkspaceToolbarButton onClick={backToList}>返回列表</WorkspaceToolbarButton>
            <button
              type="button"
              disabled={createMutation.isPending || updateMutation.isPending}
              onClick={() => void handleSave()}
              className="btn-primary h-8 px-4 text-xs disabled:opacity-60"
            >
              {createMutation.isPending || updateMutation.isPending ? "保存中..." : "保存报价"}
            </button>
          </div>
        </div>

        <p className="text-xs text-[var(--color-text-muted)]">
          选择产品后自动带出参考单价；「产品单价」「电机单价」均可手动调低。保存后点「申请生成应收」；优惠率超过老板设定上限（当前 {salesMaxDiscountPct}%）时进入审批中心待批。
          {!projectId ? (
            <>
              {" "}
              未关联项目时可前往
              <Link href="/projects" className={`mx-1 ${linkActionClass}`}>
                项目管理
              </Link>
              创建项目后再回填。
            </>
          ) : null}
        </p>
        {formError ? <p className={`text-xs ${dangerActionClass}`}>{formError}</p> : null}

        <IndustrialPanel title="基本信息">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>报价标题 *</span>
              <input
                className={fieldInputClass}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="如 XX项目设备报价"
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>客户 *</span>
              <select className={fieldInputClass} value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
                <option value="">请选择</option>
                {customerOptions.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>关联项目</span>
              <select className={fieldInputClass} value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                <option value="">不关联</option>
                {projectOptions.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>税率(%)</span>
              <input
                type="number"
                className={fieldInputClass}
                value={taxRate}
                onChange={(e) => setTaxRate(Number(e.target.value) || 0)}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>备注</span>
              <input className={fieldInputClass} value={remark} onChange={(e) => setRemark(e.target.value)} />
            </label>
          </div>
        </IndustrialPanel>

        <IndustrialPanel
          title="产品明细（联动产品库）"
          toolbar={
            <WorkspaceToolbarButton onClick={() => setLines((prev) => [...prev, emptyLine()])}>添加一行</WorkspaceToolbarButton>
          }
        >
          {motorCatalog.length === 0 && productCatalog.length > 0 ? (
            <p className="mb-2 text-xs text-[var(--color-text-muted)]">提示：尚未检测到「电机」分类产品，配套功率选项为空。请在产品库新建电机分类并录入电机。</p>
          ) : null}
          {productCatalog.length === 0 ? (
            <p className="mb-2 text-sm text-[var(--color-text-muted)]">
              暂无产品库数据，请先在
              <Link href="/products" className={`mx-1 ${linkActionClass}`}>
                产品库
              </Link>
              维护产品名称、规格型号、单位与参考售价；电机请在「电机」分类下维护功率与单价。
            </p>
          ) : null}
          <div className="overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className={tableHeaderRowClass}>
                  <th className="px-2 py-2 text-left font-normal">产品名称</th>
                  <th className="px-2 py-2 text-left font-normal">规格型号</th>
                  <th className="px-2 py-2 text-left font-normal">单位</th>
                  <th className="px-2 py-2 text-left font-normal">功率</th>
                  <th className="min-w-[120px] px-2 py-2 text-left font-normal">产品单价</th>
                  <th className="min-w-[120px] px-2 py-2 text-left font-normal">电机单价</th>
                  <th className="px-2 py-2 text-left font-normal">数量</th>
                  <th className="px-2 py-2 text-left font-normal">金额</th>
                  <th className="px-2 py-2 text-left font-normal">操作</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, idx) => {
                  const specVariants = mainProductCatalog.filter((p) => p.name === line.name);
                  const motorOptions = motorCatalog;
                  const productRef = mainProductCatalog.find((p) => p.id === line.product_id);
                  const motorRef = motorCatalog.find((p) => p.id === line.motor_product_id);
                  const rowDiscount = lineDiscount(line, mainProductCatalog, motorCatalog);
                  return (
                    <tr key={idx} className={tableBodyRowClass}>
                      <td className="px-2 py-1">
                        <select
                          className={fieldInputClass}
                          value={line.name}
                          onChange={(e) => pickProductName(idx, e.target.value)}
                        >
                          <option value="">选择产品名称</option>
                          {productModelOptions.map((name) => (
                            <option key={name} value={name}>
                              {name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-2 py-1">
                        <select
                          className={fieldInputClass}
                          value={line.product_id ?? ""}
                          disabled={!line.name}
                          onChange={(e) => pickProductSpec(idx, e.target.value)}
                        >
                          <option value="">选择规格型号</option>
                          {specVariants.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.spec || "—"}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-2 py-1">
                        <input className={fieldInputClass} value={line.unit ?? ""} readOnly placeholder="—" />
                      </td>
                      <td className="px-2 py-1">
                        <select
                          className={fieldInputClass}
                          value={line.motor_product_id ?? ""}
                          disabled={motorCatalog.length === 0}
                          onChange={(e) => pickMotorPower(idx, e.target.value)}
                        >
                          <option value="">选配电机</option>
                          {motorOptions.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} · {p.spec || "—"}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-2 py-1 align-top">
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          className={`${fieldInputClass} min-w-[108px]`}
                          value={line.unit_price}
                          disabled={!line.product_id}
                          title={line.product_id ? "可手动调低产品单价" : "请先选择规格型号"}
                          onChange={(e) => updateLine(idx, { unit_price: Number(e.target.value) || 0 })}
                        />
                        {productRef ? (
                          <div className="mt-0.5 text-[10px] text-[var(--color-text-muted)]">
                            参考 {money(productRef.reference_price)}
                            {(line.unit_price || 0) < productRef.reference_price ? (
                              <span className="ml-1 text-amber-600">
                                优惠 {money((productRef.reference_price - (line.unit_price || 0)) * (line.quantity || 0))}
                              </span>
                            ) : null}
                          </div>
                        ) : (
                          <div className="mt-0.5 text-[10px] text-[var(--color-text-muted)]">选规格后可改价</div>
                        )}
                      </td>
                      <td className="px-2 py-1 align-top">
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          className={`${fieldInputClass} min-w-[108px]`}
                          value={line.motor_unit_price || 0}
                          disabled={!line.motor_product_id}
                          title={line.motor_product_id ? "可手动调低电机单价" : "选配电机后可改价"}
                          onChange={(e) => updateLine(idx, { motor_unit_price: Number(e.target.value) || 0 })}
                        />
                        {motorRef ? (
                          <div className="mt-0.5 text-[10px] text-[var(--color-text-muted)]">
                            参考 {money(motorRef.reference_price)}
                            {(line.motor_unit_price || 0) < motorRef.reference_price ? (
                              <span className="ml-1 text-amber-600">
                                优惠 {money((motorRef.reference_price - (line.motor_unit_price || 0)) * (line.quantity || 0))}
                              </span>
                            ) : null}
                          </div>
                        ) : (
                          <div className="mt-0.5 text-[10px] text-[var(--color-text-muted)]">未选电机</div>
                        )}
                      </td>
                      <td className="px-2 py-1">
                        <input
                          type="number"
                          className={fieldInputClass}
                          value={line.quantity}
                          onChange={(e) => updateLine(idx, { quantity: Number(e.target.value) || 1 })}
                        />
                      </td>
                      <td className="px-2 py-1 text-[var(--color-text)] align-top">
                        <div>{money(lineAmount(line))}</div>
                        {rowDiscount > 0 ? (
                          <div className="text-[10px] text-amber-600">行优惠 {money(rowDiscount)}</div>
                        ) : null}
                      </td>
                      <td className="px-2 py-1">
                        <button
                          type="button"
                          className={dangerActionClass}
                          onClick={() => setLines((prev) => prev.filter((_, i) => i !== idx))}
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </IndustrialPanel>

        <IndustrialPanel title="金额汇总">
          <div className="grid gap-2 text-sm md:grid-cols-2 lg:grid-cols-4">
            <div>标准小计：{money(standardSubtotal)}</div>
            <div>成交小计：{money(subtotal)}</div>
            <div>
              税率 {taxRate}% 税额：{money(taxAmount)}
            </div>
            <div className="font-semibold text-[var(--color-primary)]">含税总计：{money(finalTotal)}</div>
            {discountFinalTotal > 0 ? (
              <div className="text-amber-600 md:col-span-2 lg:col-span-4">
                整单优惠 {money(discountFinalTotal)}（{discountRatePct.toFixed(2)}%）
                {needsBossForDiscount
                  ? `，超过销售免审上限 ${salesMaxDiscountPct}%，申请应收后需老板在审批中心通过`
                  : `，在免审上限 ${salesMaxDiscountPct}% 内，申请应收后销售可直接确认`}
              </div>
            ) : (
              <div className="text-[var(--color-text-muted)] md:col-span-2 lg:col-span-4">
                当前无优惠，申请应收可直接确认
              </div>
            )}
          </div>
        </IndustrialPanel>

        {quoteReceivableEnabled && editId ? (
          <IndustrialPanel title="应收申请">
            <div className="space-y-2 text-sm">
              <p className="text-[var(--color-text-muted)]">
                当前状态：{RECEIVABLE_LABEL[detailReceivableStatus] ?? detailReceivableStatus}
              </p>
              {receivableRequest ? (
                <div className="grid gap-1 text-xs text-[var(--color-text-muted)] md:grid-cols-2">
                  <div>标准金额：{money(Number(receivableRequest.standard_amount))}</div>
                  <div>申请应收：{money(Number(receivableRequest.requested_amount))}</div>
                  <div>优惠金额：{money(Number(receivableRequest.discount_amount))}</div>
                  <div>
                    审批状态：
                    {receivableRequest.approval_status === "pending"
                      ? "待老板审批"
                      : receivableRequest.approval_status === "approved"
                        ? "已通过"
                        : receivableRequest.approval_status === "rejected"
                          ? "已驳回"
                          : receivableRequest.approval_status}
                  </div>
                  {receivableRequest.reject_reason ? (
                    <div className="md:col-span-2 text-red-500">驳回原因：{receivableRequest.reject_reason}</div>
                  ) : null}
                </div>
              ) : null}
              {receivableError ? <p className="text-xs text-red-500">{receivableError}</p> : null}
              <div className="flex flex-wrap gap-2">
                {canPostQuote && detailReceivableStatus === "none" && !receivableRequest ? (
                  <button
                    type="button"
                    className="btn-primary h-8 px-4 text-xs disabled:opacity-60"
                    disabled={createReceivableMutation.isPending}
                    onClick={() => void handleApplyReceivable()}
                  >
                    {createReceivableMutation.isPending ? "提交中..." : "申请生成应收"}
                  </button>
                ) : null}
                {canConfirmReceivable &&
                receivableRequest &&
                receivableRequest.approval_status === "approved" &&
                !receivableRequest.receivable_entry_id ? (
                  <button
                    type="button"
                    className="btn-primary h-8 px-4 text-xs disabled:opacity-60"
                    disabled={confirmReceivableMutation.isPending}
                    onClick={() => void handleConfirmReceivable()}
                  >
                    {confirmReceivableMutation.isPending ? "确认中..." : "确认应收"}
                  </button>
                ) : null}
                {detailReceivableStatus === "posted" ? (
                  <Link href="/accounting" className={linkActionClass}>
                    查看收支台账
                  </Link>
                ) : null}
                {receivableRequest?.approval_status === "pending" ? (
                  <span className="text-xs text-amber-600">
                    优惠待批，请老板前往
                    <Link href="/approvals" className={`mx-1 ${linkActionClass}`}>
                      审批中心
                    </Link>
                    处理
                  </span>
                ) : null}
              </div>
            </div>
          </IndustrialPanel>
        ) : null}
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md" fill>
      <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)]">
        <span>对客报价面向客户销售，产品明细联动产品库名称、规格、单位与配套电机。</span>
        <Link href="/quotes" className={linkActionClass}>
          返回内部报价/BOM
        </Link>
      </div>
      <MasterListPage<ListRow>
        embedded
        fill
        title="对客报价"
        persistenceKey="customer-quotes-v1"
        exportFilename="customer-quotes"
        columns={[
          { key: "quoteNo", title: "报价编号", canView: true, fixed: "left", width: 160 },
          { key: "title", title: "标题", canView: true, width: 200 },
          { key: "finalTotal", title: "含税总额", canView: true },
          { key: "receivableStatus", title: "应收", canView: true, width: 100 },
          { key: "status", title: "状态", canView: true, width: 80 },
        ]}
        rows={rows}
        total={listData.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={listQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-2">
            <button type="button" className={linkActionClass} onClick={() => openEdit(row.id)}>
              编辑
            </button>
            <button type="button" className={dangerActionClass} onClick={() => void handleDelete(row.id, row.title)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreate}>新建对客报价</WorkspaceToolbarButton>}
        emptyHint="暂无对客报价，点击右上角新建，从产品库选择名称与规格型号。"
      />
    </IndustrialPage>
  );
}
