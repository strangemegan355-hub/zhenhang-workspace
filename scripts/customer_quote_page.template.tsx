"use client";

import { MasterListPage } from "@/components/master/master-list-page";
import {
  useBusinessSettingsQuery,
  useCreateCustomerQuoteMutation,
  useCustomersQuery,
  useDeleteCustomerQuoteMutation,
  useProductCategoriesQuery,
  useProductsQuery,
  useProjectsQuery,
  useQuoteDetailQuery,
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

type ListRow = {
  id: string;
  quoteNo: string;
  title: string;
  finalTotal: string;
  status: string;
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

export default function CustomerQuotePage() {
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
  const createMutation = useCreateCustomerQuoteMutation();
  const updateMutation = useUpdateCustomerQuoteMutation();
  const deleteMutation = useDeleteCustomerQuoteMutation();

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
        label: `${String(p.project_no ?? "")}@@dot@@${String(p.name ?? "")}`,
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
        status: String(row.workflow_state ?? "draft") === "draft" ? "@@draft@@" : String(row.workflow_state ?? ""),
      })),
    [listData.items],
  );

  const subtotal = useMemo(() => lines.reduce((sum, line) => sum + lineAmount(line), 0), [lines]);
  const taxAmount = useMemo(() => (subtotal * taxRate) / 100, [subtotal, taxRate]);
  const finalTotal = useMemo(() => subtotal + taxAmount, [subtotal, taxRate]);

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
      setFormError("@@err_title@@");
      return;
    }
    if (!customerId) {
      setFormError("@@err_customer@@");
      return;
    }
    const validLines = lines.filter((l) => l.name.trim());
    if (!validLines.length) {
      setFormError("@@err_lines@@");
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
      setFormError(err instanceof Error ? err.message : "@@err_save@@");
    }
  };

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`@@confirm_delete@@`.replace("{label}", label))) return;
    try {
      await deleteMutation.mutateAsync(id);
      void listQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "@@err_delete@@");
    }
  };

  if (mode === "edit") {
    if (editId && !detailQuery.data) {
      return (
        <IndustrialPage gap="md" fill>
          <IndustrialPanel fill title="@@loading_title@@">
            <p className="text-sm text-[var(--color-text-muted)]">@@loading@@</p>
          </IndustrialPanel>
        </IndustrialPage>
      );
    }

    return (
      <IndustrialPage gap="md" fill>
        <div className="flex items-center justify-between gap-2">
          <h2 className={typography.pageTitle}>{editId ? "@@edit_title@@" : "@@new_title@@"}</h2>
          <div className="flex gap-2">
            <WorkspaceToolbarButton onClick={backToList}>@@back_list@@</WorkspaceToolbarButton>
            <button
              type="button"
              disabled={createMutation.isPending || updateMutation.isPending}
              onClick={() => void handleSave()}
              className="btn-primary h-8 px-4 text-xs disabled:opacity-60"
            >
              {createMutation.isPending || updateMutation.isPending ? "@@saving@@" : "@@save_quote@@"}
            </button>
          </div>
        </div>

        <p className="text-xs text-[var(--color-text-muted)]">
          @@hint_link@@
          {!projectId ? (
            <>
              {" "}
              @@hint_no_project@@
              <Link href="/projects" className={`mx-1 ${linkActionClass}`}>
                @@projects@@
              </Link>
              @@hint_after_project@@
            </>
          ) : null}
        </p>
        {formError ? <p className={`text-xs ${dangerActionClass}`}>{formError}</p> : null}

        <IndustrialPanel title="@@basic_info@@">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>@@label_title@@</span>
              <input
                className={fieldInputClass}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="@@ph_title@@"
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>@@label_customer@@</span>
              <select className={fieldInputClass} value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
                <option value="">@@please_select@@</option>
                {customerOptions.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>@@label_project@@</span>
              <select className={fieldInputClass} value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                <option value="">@@no_project@@</option>
                {projectOptions.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>@@label_tax@@</span>
              <input
                type="number"
                className={fieldInputClass}
                value={taxRate}
                onChange={(e) => setTaxRate(Number(e.target.value) || 0)}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>@@label_remark@@</span>
              <input className={fieldInputClass} value={remark} onChange={(e) => setRemark(e.target.value)} />
            </label>
          </div>
        </IndustrialPanel>

        <IndustrialPanel
          title="@@lines_title@@"
          toolbar={
            <WorkspaceToolbarButton onClick={() => setLines((prev) => [...prev, emptyLine()])}>@@add_line@@</WorkspaceToolbarButton>
          }
        >
          {motorCatalog.length === 0 && productCatalog.length > 0 ? (
            <p className="mb-2 text-xs text-[var(--color-text-muted)]">@@empty_motor_hint@@</p>
          ) : null}
          {productCatalog.length === 0 ? (
            <p className="mb-2 text-sm text-[var(--color-text-muted)]">
              @@empty_catalog_1@@
              <Link href="/products" className={`mx-1 ${linkActionClass}`}>
                @@products@@
              </Link>
              @@empty_catalog_2@@
            </p>
          ) : null}
          <div className="overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className={tableHeaderRowClass}>
                  <th className="px-2 py-2 text-left font-normal">@@col_name@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_spec@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_unit@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_power@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_price@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_qty@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_amount@@</th>
                  <th className="px-2 py-2 text-left font-normal">@@col_action@@</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, idx) => {
                  const specVariants = mainProductCatalog.filter((p) => p.name === line.name);
                  const motorOptions = motorCatalog;
                  return (
                    <tr key={idx} className={tableBodyRowClass}>
                      <td className="px-2 py-1">
                        <select
                          className={fieldInputClass}
                          value={line.name}
                          onChange={(e) => pickProductName(idx, e.target.value)}
                        >
                          <option value="">@@sel_name@@</option>
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
                          <option value="">@@sel_spec@@</option>
                          {specVariants.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.spec || "@@default_spec@@"}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-2 py-1">
                        <input className={fieldInputClass} value={line.unit ?? ""} readOnly placeholder="@@default_spec@@" />
                      </td>
                      <td className="px-2 py-1">
                        <select
                          className={fieldInputClass}
                          value={line.motor_product_id ?? ""}
                          disabled={motorCatalog.length === 0}
                          onChange={(e) => pickMotorPower(idx, e.target.value)}
                        >
                          <option value="">@@sel_motor@@</option>
                          {motorOptions.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name}@@dot@@{p.spec || "@@default_spec@@"}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-2 py-1">
                        <input
                          type="number"
                          className={fieldInputClass}
                          value={line.unit_price}
                          onChange={(e) => updateLine(idx, { unit_price: Number(e.target.value) || 0 })}
                        />
                      </td>
                      <td className="px-2 py-1">
                        <input
                          type="number"
                          className={fieldInputClass}
                          value={line.quantity}
                          onChange={(e) => updateLine(idx, { quantity: Number(e.target.value) || 1 })}
                        />
                      </td>
                      <td className="px-2 py-1 text-[var(--color-text)]">
                        <div>{money(lineAmount(line))}</div>
                        {(line.motor_unit_price || 0) > 0 ? (
                          <div className="text-[10px] text-[var(--color-text-muted)]">
                            @@motor_amount_prefix@@{money((line.motor_unit_price || 0) * (line.quantity || 0))}
                          </div>
                        ) : null}
                      </td>
                      <td className="px-2 py-1">
                        <button
                          type="button"
                          className={dangerActionClass}
                          onClick={() => setLines((prev) => prev.filter((_, i) => i !== idx))}
                        >
                          @@delete@@
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </IndustrialPanel>

        <IndustrialPanel title="@@summary@@">
          <div className="grid gap-2 text-sm md:grid-cols-2 lg:grid-cols-4">
            <div>@@subtotal@@{money(subtotal)}</div>
            <div>
              @@tax_prefix@@{taxRate}@@tax_suffix@@{money(taxAmount)}
            </div>
            <div className="font-semibold text-[var(--color-primary)]">@@total@@{money(finalTotal)}</div>
          </div>
        </IndustrialPanel>
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md" fill>
      <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)]">
        <span>@@list_hint@@</span>
        <Link href="/quotes" className={linkActionClass}>
          @@back_internal@@
        </Link>
      </div>
      <MasterListPage<ListRow>
        embedded
        fill
        title="@@page_title@@"
        persistenceKey="customer-quotes-v1"
        exportFilename="customer-quotes"
        columns={[
          { key: "quoteNo", title: "@@col_quote_no@@", canView: true, fixed: "left", width: 160 },
          { key: "title", title: "@@col_title@@", canView: true, width: 200 },
          { key: "finalTotal", title: "@@col_final@@", canView: true },
          { key: "status", title: "@@col_status@@", canView: true, width: 80 },
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
              @@edit@@
            </button>
            <button type="button" className={dangerActionClass} onClick={() => void handleDelete(row.id, row.title)}>
              @@delete@@
            </button>
          </div>
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreate}>@@new_btn@@</WorkspaceToolbarButton>}
        emptyHint="@@empty_hint@@"
      />
    </IndustrialPage>
  );
}
