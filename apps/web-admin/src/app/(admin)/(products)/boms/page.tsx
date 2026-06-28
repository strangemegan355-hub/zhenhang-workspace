"use client";

import { DataGrid } from "@zhenhang/data-grid";
import {
  useBomItemsQuery,
  useBomsListQuery,
  useCreateBomItemMutation,
  useCreateBomMutation,
  useImportBomItemsMutation,
  useMachinesQuery,
} from "@zhenhang/query-hooks";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { buildBomImportTemplateXlsx, parseBomFile } from "@/lib/bom-import";
import {
  EmptyState,
  ErrorBanner,
  IndustrialPage,
  IndustrialPanel,
  TableSkeleton,
  WorkspaceToolbarButton,
  typography,
} from "@zhenhang/ui";
import { useMemo, useRef, useState } from "react";

type BomRow = {
  id: string;
  version: string;
  machineLabel: string;
  status: string;
  totalCost: string;
  isActive: string;
};

const bomFormDefault = {
  machine_id: "",
  version: "V1.0",
  is_active: true,
  remark: "",
};

const SUBSYSTEM_OPTIONS = [
  { value: "mechanical", label: "机械 system" },
  { value: "electrical", label: "电气 system" },
  { value: "hydraulic", label: "液压 system" },
  { value: "pneumatic", label: "气动 system" },
  { value: "control", label: "控制/电控" },
];

const itemFormDefault = {
  item_code: "",
  item_name: "",
  unit: "EA",
  quantity: "1",
  unit_cost: "0",
  subsystem: "",
};

export default function BomsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedBomId, setSelectedBomId] = useState<string | null>(null);
  const [itemsPage, setItemsPage] = useState(1);
  const [showBomCreate, setShowBomCreate] = useState(false);
  const [showItemCreate, setShowItemCreate] = useState(false);
  const [bomForm, setBomForm] = useState(bomFormDefault);
  const [itemForm, setItemForm] = useState(itemFormDefault);
  const [bomError, setBomError] = useState<string | null>(null);
  const [itemError, setItemError] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [importInfo, setImportInfo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const machinesQuery = useMachinesQuery(1);
  const listQuery = useBomsListQuery(page, search.trim() || undefined);
  const itemsQuery = useBomItemsQuery(selectedBomId, itemsPage);
  const createBom = useCreateBomMutation();
  const createItem = useCreateBomItemMutation();
  const importItems = useImportBomItemsMutation();

  const listData = (listQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const itemsData = (itemsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const machineItems = useMemo(
    () => (machinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [],
    [machinesQuery.data],
  );

  const machineOptions = useMemo(
    () =>
      machineItems.map((m) => ({
        value: String(m.id ?? ""),
        label: `${m.code ?? m.machine_code ?? ""} · ${m.name ?? ""}`,
      })),
    [machineItems],
  );

  const machineLabelById = useMemo(() => {
    const map = new Map<string, string>();
    for (const m of machineItems) {
      map.set(String(m.id ?? ""), `${m.code ?? m.machine_code ?? ""} · ${m.name ?? ""}`);
    }
    return map;
  }, [machineItems]);

  const bomRows = useMemo(
    () =>
      (listData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        version: String(row.version ?? ""),
        machineLabel: machineLabelById.get(String(row.machine_id ?? "")) ?? String(row.machine_id ?? ""),
        status: String(row.status ?? ""),
        totalCost: String(row.total_cost ?? "0"),
        isActive: row.is_active ? "是" : "否",
      })),
    [listData.items, machineLabelById],
  );

  const itemRows = useMemo(
    () =>
      (itemsData.items ?? []).map((row) => ({
        id: String(row.id ?? row.item_code ?? ""),
        itemCode: String(row.item_code ?? ""),
        itemName: String(row.item_name ?? ""),
        subsystem: String(row.subsystem ?? ""),
        quantity: String(row.quantity ?? ""),
        unitCost: String(row.unit_cost ?? ""),
        lineTotal: String(row.line_total ?? ""),
      })),
    [itemsData.items],
  );

  const handleCreateBom = async () => {
    setBomError(null);
    if (!bomForm.machine_id || !bomForm.version.trim()) {
      setBomError("请选择机型并填写 BOM 版本号");
      return;
    }
    try {
      const created = await createBom.mutateAsync({
        machine_id: bomForm.machine_id,
        version: bomForm.version.trim(),
        is_active: Boolean(bomForm.is_active),
        remark: bomForm.remark.trim() || undefined,
        status: "draft",
      });
      setBomForm(bomFormDefault);
      setShowBomCreate(false);
      setSelectedBomId(String(created.id ?? ""));
      void listQuery.refetch();
    } catch (err) {
      setBomError(err instanceof Error ? err.message : "创建 BOM 失败");
    }
  };

  const handleCreateItem = async () => {
    setItemError(null);
    if (!selectedBomId) return;
    if (!itemForm.item_code.trim() || !itemForm.item_name.trim()) {
      setItemError("请填写物料编码和名称");
      return;
    }
    try {
      await createItem.mutateAsync({
        bom_id: selectedBomId,
        item_code: itemForm.item_code.trim(),
        item_name: itemForm.item_name.trim(),
        unit: itemForm.unit.trim() || "EA",
        quantity: Number(itemForm.quantity) || 1,
        unit_cost: Number(itemForm.unit_cost) || 0,
        subsystem: itemForm.subsystem || undefined,
      });
      setItemForm(itemFormDefault);
      setShowItemCreate(false);
      void itemsQuery.refetch();
      void listQuery.refetch();
    } catch (err) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? String((err as { response?: { data?: { message?: string } } }).response?.data?.message ?? "添加 BOM 明细失败")
          : err instanceof Error
            ? err.message
            : "添加 BOM 明细失败";
      setItemError(msg);
    }
  };

  const handleImportFile = async (file: File) => {
    setImportError(null);
    setImportInfo(null);
    if (!selectedBomId) {
      setImportError("请先选择 BOM");
      return;
    }
    try {
      const rows = await parseBomFile(file);
      if (!rows.length) {
        setImportError("未识别到有效数据，请使用 Excel 模板（表头：物料编码, 物料名称, 单位, 数量, 单位成本）");
        return;
      }
      await importItems.mutateAsync({ bom_id: selectedBomId, items: rows });
      setImportInfo(`已成功导入 ${rows.length} 条物料`);
      void itemsQuery.refetch();
      void listQuery.refetch();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "导入失败，请检查文件格式");
    }
  };

  const downloadImportTemplate = () => {
    const blob = buildBomImportTemplateXlsx();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "bom-import-template.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <IndustrialPage gap="md" fill>
      {showBomCreate ? (
        <MasterCreateForm
          title="新增 BOM 清单"
          fields={[
            {
              key: "machine_id",
              label: "所属机型",
              type: "select",
              required: true,
              options: machineOptions,
            },
            { key: "version", label: "BOM 版本", required: true, placeholder: "如 V1.0" },
            { key: "is_active", label: "设为当前版本", type: "checkbox" },
            { key: "remark", label: "备注", placeholder: "可选" },
          ]}
          values={bomForm}
          onChange={(key, value) => setBomForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleCreateBom()}
          onCancel={() => {
            setShowBomCreate(false);
            setBomError(null);
          }}
          submitting={createBom.isPending}
          error={bomError}
        />
      ) : null}

      <MasterListPage<BomRow>
        embedded
        title="BOM 管理"
        persistenceKey="master-boms-v1"
        exportFilename="boms"
        columns={[
          { key: "version", title: "版本", canView: true, fixed: "left", width: 100 },
          { key: "machineLabel", title: "所属机型", canView: true, width: 280 },
          { key: "status", title: "状态", canView: true },
          { key: "totalCost", title: "总成本", canView: true },
          { key: "isActive", title: "当前版本", canView: true },
        ]}
        rows={bomRows}
        total={listData.total ?? bomRows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={listQuery}
        rowKey={(row) => row.id}
        onRowClick={(row) => {
          setSelectedBomId(row.id);
          setShowItemCreate(false);
        }}
        toolbarExtra={
          <WorkspaceToolbarButton onClick={() => setShowBomCreate(true)}>新增 BOM</WorkspaceToolbarButton>
        }
        emptyHint="请先在「机型管理」新增设备，再在此创建 BOM"
      />

      {selectedBomId ? (
        <IndustrialPanel
          fill
          title="BOM 明细"
          inlineLoading={itemsQuery.isFetching && !itemsQuery.isLoading}
          toolbar={
            <div className="flex flex-wrap gap-2">
              <WorkspaceToolbarButton onClick={() => setShowItemCreate(true)}>添加物料</WorkspaceToolbarButton>
              <WorkspaceToolbarButton
                loading={importItems.isPending}
                onClick={() => fileInputRef.current?.click()}
              >
                从 Excel 导入
              </WorkspaceToolbarButton>
              <WorkspaceToolbarButton onClick={downloadImportTemplate}>下载 Excel 模板</WorkspaceToolbarButton>
              <WorkspaceToolbarButton onClick={() => setSelectedBomId(null)} keyboardHint="Esc" title="关闭明细">
                关闭
              </WorkspaceToolbarButton>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv,.txt,.tsv"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleImportFile(file);
                  e.target.value = "";
                }}
              />
            </div>
          }
        >
          {importError ? <p className="mb-2 text-xs text-red-500">{importError}</p> : null}
          {importInfo ? <p className="mb-2 text-xs text-emerald-600">{importInfo}</p> : null}
          {showItemCreate ? (
            <div className="mb-4">
              <MasterCreateForm
                title="添加 BOM 物料行"
                fields={[
                  { key: "item_code", label: "物料编码", required: true, placeholder: "如 SCREW-M30" },
                  { key: "item_name", label: "物料名称", required: true, placeholder: "如 螺杆总成" },
                  { key: "subsystem", label: "子系统", type: "select", options: SUBSYSTEM_OPTIONS },
                  { key: "unit", label: "单位", placeholder: "EA" },
                  { key: "quantity", label: "数量", type: "number", required: true },
                  { key: "unit_cost", label: "单位成本", type: "number" },
                ]}
                values={itemForm}
                onChange={(key, value) => setItemForm((s) => ({ ...s, [key]: value }))}
                onSubmit={() => void handleCreateItem()}
                onCancel={() => {
                  setShowItemCreate(false);
                  setItemError(null);
                }}
                submitting={createItem.isPending}
                error={itemError}
                submitLabel="添加"
              />
            </div>
          ) : null}

          {itemsQuery.isLoading ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <TableSkeleton rows={8} cols={5} />
            </div>
          ) : itemsQuery.isError ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <ErrorBanner message="无法加载 BOM 明细。" onRetry={() => itemsQuery.refetch()} />
            </div>
          ) : itemRows.length === 0 ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <EmptyState message="该 BOM 暂无明细，点击「添加物料」录入清单" />
            </div>
          ) : (
            <DataGrid
              columns={[
                { key: "itemCode", title: "物料编码", canView: true, fixed: "left", width: 140 },
                { key: "itemName", title: "物料名称", canView: true, width: 200 },
                { key: "subsystem", title: "子系统", canView: true, width: 100 },
                { key: "quantity", title: "数量", canView: true },
                { key: "unitCost", title: "单位成本", canView: true },
                { key: "lineTotal", title: "行合计", canView: true },
              ]}
              rows={itemRows}
              rowKey={(row) => row.id}
              page={itemsPage}
              total={itemsData.total ?? itemRows.length}
              pageSize={100}
              onPageChange={setItemsPage}
              persistenceKey={`bom-items-${selectedBomId}`}
              emptyMessage="暂无 BOM 明细"
            />
          )}
        </IndustrialPanel>
      ) : (
        <p className={`${typography.caption} text-center`}>选择上方 BOM 行查看明细，或点击「新增 BOM」创建清单</p>
      )}
    </IndustrialPage>
  );
}
