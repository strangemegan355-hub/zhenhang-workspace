"use client";

import {
  useCreateMaterialCategoryMutation,
  useCreateUnitMutation,
  useDeleteMaterialCategoryMutation,
  useDeleteUnitMutation,
  useMaterialCategoriesQuery,
  useUnitsQuery,
  useUpdateMaterialCategoryMutation,
  useUpdateUnitMutation,
} from "@zhenhang/query-hooks";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { batchDeleteRows } from "@/components/master/master-row-actions";
import { autoMasterCode } from "@/lib/auto-master-code";
import { masterNameCol, masterRemarkCol } from "@/lib/master-grid-columns";
import { IndustrialPage, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";

type UnitRow = { id: string; name: string; remark: string };
type CategoryRow = { id: string; name: string; scope: string; remark: string };

const emptyUnitForm = { name: "", remark: "" };
const emptyCatForm = { name: "", scope: "", remark: "" };

function RowActions({
  onEdit,
  onDelete,
}: {
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <button type="button" className="text-xs text-blue-400 hover:underline" onClick={onEdit}>
        修改
      </button>
      <button type="button" className="text-xs text-red-400 hover:underline" onClick={onDelete}>
        删除
      </button>
    </div>
  );
}

export default function StandardsPage() {
  const [unitPage, setUnitPage] = useState(1);
  const [unitSearch, setUnitSearch] = useState("");
  const [catPage, setCatPage] = useState(1);
  const [catSearch, setCatSearch] = useState("");
  const [unitEditId, setUnitEditId] = useState<string | null>(null);
  const [catEditId, setCatEditId] = useState<string | null>(null);
  const [showUnitForm, setShowUnitForm] = useState(false);
  const [showCatForm, setShowCatForm] = useState(false);
  const [unitForm, setUnitForm] = useState(emptyUnitForm);
  const [catForm, setCatForm] = useState(emptyCatForm);
  const [unitError, setUnitError] = useState<string | null>(null);
  const [catError, setCatError] = useState<string | null>(null);

  const unitsQuery = useUnitsQuery(unitPage, unitSearch.trim() || undefined);
  const catsQuery = useMaterialCategoriesQuery(catPage, catSearch.trim() || undefined);
  const createUnit = useCreateUnitMutation();
  const updateUnit = useUpdateUnitMutation();
  const deleteUnit = useDeleteUnitMutation();
  const createCat = useCreateMaterialCategoryMutation();
  const updateCat = useUpdateMaterialCategoryMutation();
  const deleteCat = useDeleteMaterialCategoryMutation();

  const unitData = (unitsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const catData = (catsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const unitRows = useMemo(
    () =>
      (unitData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        remark: String(row.remark ?? ""),
      })),
    [unitData.items],
  );

  const catRows = useMemo(
    () =>
      (catData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        name: String(row.name ?? ""),
        scope: String(row.scope ?? ""),
        remark: String(row.remark ?? ""),
      })),
    [catData.items],
  );

  const closeUnitForm = () => {
    setShowUnitForm(false);
    setUnitEditId(null);
    setUnitForm(emptyUnitForm);
    setUnitError(null);
  };

  const closeCatForm = () => {
    setShowCatForm(false);
    setCatEditId(null);
    setCatForm(emptyCatForm);
    setCatError(null);
  };

  const openCreateUnit = () => {
    closeCatForm();
    setUnitEditId(null);
    setUnitForm(emptyUnitForm);
    setShowUnitForm(true);
  };

  const openEditUnit = (row: UnitRow) => {
    closeCatForm();
    setUnitEditId(row.id);
    setUnitForm({ name: row.name, remark: row.remark });
    setShowUnitForm(true);
    setUnitError(null);
  };

  const openCreateCat = () => {
    closeUnitForm();
    setCatEditId(null);
    setCatForm(emptyCatForm);
    setShowCatForm(true);
  };

  const openEditCat = (row: CategoryRow) => {
    closeUnitForm();
    setCatEditId(row.id);
    setCatForm({ name: row.name, scope: row.scope, remark: row.remark });
    setShowCatForm(true);
    setCatError(null);
  };

  const handleSaveUnit = async () => {
    setUnitError(null);
    if (!unitForm.name.trim()) {
      setUnitError("请填写单位名称");
      return;
    }
    const code =
      /^[A-Za-z0-9/]+$/.test(unitForm.name.trim()) && unitForm.name.trim().length <= 12
        ? unitForm.name.trim().toUpperCase().replace(/\//g, "")
        : autoMasterCode(unitForm.name.trim(), "U");
    const body = {
      code,
      name: unitForm.name.trim(),
      remark: unitForm.remark.trim() || undefined,
    };
    try {
      if (unitEditId) {
        await updateUnit.mutateAsync({
          id: unitEditId,
          body: { name: unitForm.name.trim(), remark: unitForm.remark.trim() || undefined },
        });
      } else {
        await createUnit.mutateAsync(body);
      }
      closeUnitForm();
      void unitsQuery.refetch();
    } catch (err) {
      setUnitError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteUnit = async (id: string, label: string) => {
    if (!window.confirm(`确认删除计量单位「${label}」？`)) return;
    try {
      await deleteUnit.mutateAsync(id);
      if (unitEditId === id) closeUnitForm();
      void unitsQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleSaveCat = async () => {
    setCatError(null);
    if (!catForm.name.trim()) {
      setCatError("请填写分类名称");
      return;
    }
    const body = {
      code: autoMasterCode(catForm.name.trim(), "MC"),
      name: catForm.name.trim(),
      scope: catForm.scope.trim() || undefined,
      remark: catForm.remark.trim() || undefined,
    };
    try {
      if (catEditId) {
        await updateCat.mutateAsync({
          id: catEditId,
          body: {
            name: catForm.name.trim(),
            scope: catForm.scope.trim() || undefined,
            remark: catForm.remark.trim() || undefined,
          },
        });
      } else {
        await createCat.mutateAsync(body);
      }
      closeCatForm();
      void catsQuery.refetch();
    } catch (err) {
      setCatError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteCat = async (id: string, label: string) => {
    if (!window.confirm(`确认删除材料分类「${label}」？`)) return;
    try {
      await deleteCat.mutateAsync(id);
      if (catEditId === id) closeCatForm();
      void catsQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  const unitSubmitting = createUnit.isPending || updateUnit.isPending;
  const catSubmitting = createCat.isPending || updateCat.isPending;

  const handleBatchDeleteUnits = async (selected: UnitRow[]) => {
    await batchDeleteRows(selected, (id) => deleteUnit.mutateAsync(id), () => void unitsQuery.refetch());
  };

  const handleBatchDeleteCats = async (selected: CategoryRow[]) => {
    await batchDeleteRows(selected, (id) => deleteCat.mutateAsync(id), () => void catsQuery.refetch());
  };

  return (
    <IndustrialPage gap="md" fill>
      {showUnitForm ? (
        <MasterCreateForm
          title={unitEditId ? "修改计量单位" : "新增计量单位"}
          fields={[
            { key: "name", label: "单位名称", required: true, placeholder: "如 个/件、EA、KG" },
            { key: "remark", label: "备注" },
          ]}
          values={unitForm}
          onChange={(key, value) => setUnitForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveUnit()}
          onCancel={closeUnitForm}
          submitting={unitSubmitting}
          error={unitError}
          submitLabel={unitEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {showCatForm ? (
        <MasterCreateForm
          title={catEditId ? "修改材料分类" : "新增材料分类"}
          fields={[
            { key: "name", label: "分类名称", required: true, placeholder: "如 钢材" },
            { key: "scope", label: "适用范围", placeholder: "如 结构件/板材" },
            { key: "remark", label: "备注" },
          ]}
          values={catForm}
          onChange={(key, value) => setCatForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveCat()}
          onCancel={closeCatForm}
          submitting={catSubmitting}
          error={catError}
          submitLabel={catEditId ? "保存修改" : "保存"}
        />
      ) : null}

      <MasterListPage<UnitRow>
        embedded
        fill
        title="计量单位"
        persistenceKey="master-units-v1"
        exportFilename="units"
        columns={[masterNameCol(), masterRemarkCol()]}
        rows={unitRows}
        total={unitData.total ?? unitRows.length}
        page={unitPage}
        onPageChange={setUnitPage}
        search={unitSearch}
        onSearchChange={setUnitSearch}
        query={unitsQuery}
        rowKey={(row) => row.id}
        onBatchDelete={handleBatchDeleteUnits}
        rowActions={(row) => (
          <RowActions
            onEdit={() => openEditUnit(row)}
            onDelete={() => void handleDeleteUnit(row.id, row.name)}
          />
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreateUnit}>新增单位</WorkspaceToolbarButton>}
        emptyHint="材料库等单位字段从此处选用，可先维护 EA、KG 等常用单位"
      />

      <MasterListPage<CategoryRow>
        embedded
        fill
        title="材料分类"
        persistenceKey="master-material-categories-v1"
        exportFilename="material-categories"
        columns={[masterNameCol(), { key: "scope", title: "适用范围", canView: true, width: 160 }]}
        rows={catRows}
        total={catData.total ?? catRows.length}
        page={catPage}
        onPageChange={setCatPage}
        search={catSearch}
        onSearchChange={setCatSearch}
        query={catsQuery}
        rowKey={(row) => row.id}
        onBatchDelete={handleBatchDeleteCats}
        rowActions={(row) => (
          <RowActions
            onEdit={() => openEditCat(row)}
            onDelete={() => void handleDeleteCat(row.id, row.name)}
          />
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreateCat}>新增分类</WorkspaceToolbarButton>}
        emptyHint="材料录入时分类从此处选用，如钢材、外购件、铸件"
      />
    </IndustrialPage>
  );
}
