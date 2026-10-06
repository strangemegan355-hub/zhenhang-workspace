"use client";

import { useToastStore } from "@zhenhang/realtime";

import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import {
  useCreateMachineCategoryMutation,
  useCreateMachineImageMutation,
  useCreateMachineMutation,
  useCreateMachineParameterMutation,
  useDeleteMachineCategoryMutation,
  useDeleteMachineImageMutation,
  useDeleteMachineMutation,
  useDeleteMachineParameterMutation,
  useMachineCategoriesQuery,
  useMachineImagesQuery,
  useMachineParametersQuery,
  useMachinesQuery,
  useUpdateMachineCategoryMutation,
  useUpdateMachineImageMutation,
  useUpdateMachineMutation,
  useUpdateMachineParameterMutation,
} from "@zhenhang/query-hooks";
import { IndustrialPage, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState, type ReactNode } from "react";
import { searchInputClass } from "@/lib/form-styles";
import OptionGroupsSection from "@/components/machines/option-groups-section";

type CategoryRow = { id: string; code: string; name: string; description: string };
type MachineRow = {
  id: string;
  code: string;
  name: string;
  modelNo: string;
  status: string;
  statusLabel: string;
  categoryLabel: string;
  categoryId: string;
  description: string;
};
type ParamRow = {
  id: string;
  paramKey: string;
  paramName: string;
  value: string;
  unit: string;
  remarks: string;
};
type ImageRow = { id: string; fileUrl: string; fileName: string; sortOrder: string };

const STATUS_OPTIONS = [
  { value: "draft", label: "草稿" },
  { value: "active", label: "启用" },
];

const STATUS_LABEL: Record<string, string> = { draft: "草稿", active: "启用" };

const emptyCategoryForm = { code: "", name: "", description: "" };
const emptyMachineForm = {
  category_id: "",
  code: "",
  name: "",
  model_no: "",
  status: "draft",
  description: "",
};
const emptyParamForm = { param_key: "", param_name: "", value: "", unit: "", remarks: "" };
const emptyImageForm = { file_url: "", file_name: "", sort_order: "0" };

function RowActions({
  onEdit,
  onDelete,
  extra,
}: {
  onEdit: () => void;
  onDelete: () => void;
  extra?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-2">
      <button type="button" className="text-xs text-blue-400 hover:underline" onClick={onEdit}>
        修改
      </button>
      {extra}
      <button type="button" className="text-xs text-red-400 hover:underline" onClick={onDelete}>
        删除
      </button>
    </div>
  );
}

function MachineSelect({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (id: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <select
      className={searchInputClass}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">请选择机型</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export default function MachinesPage() {
  const [catPage, setCatPage] = useState(1);
  const [catSearch, setCatSearch] = useState("");
  const [machinePage, setMachinePage] = useState(1);
  const [machineSearch, setMachineSearch] = useState("");
  const [paramPage, setParamPage] = useState(1);
  const [paramSearch, setParamSearch] = useState("");
  const [imagePage, setImagePage] = useState(1);
  const [imageSearch, setImageSearch] = useState("");
  const [selectedMachineId, setSelectedMachineId] = useState("");

  const [catEditId, setCatEditId] = useState<string | null>(null);
  const [machineEditId, setMachineEditId] = useState<string | null>(null);
  const [paramEditId, setParamEditId] = useState<string | null>(null);
  const [imageEditId, setImageEditId] = useState<string | null>(null);

  const [showCatForm, setShowCatForm] = useState(false);
  const [showMachineForm, setShowMachineForm] = useState(false);
  const [showParamForm, setShowParamForm] = useState(false);
  const [showImageForm, setShowImageForm] = useState(false);

  const [catForm, setCatForm] = useState(emptyCategoryForm);
  const [machineForm, setMachineForm] = useState(emptyMachineForm);
  const [paramForm, setParamForm] = useState(emptyParamForm);
  const [imageForm, setImageForm] = useState(emptyImageForm);

  const [catError, setCatError] = useState<string | null>(null);
  const [machineError, setMachineError] = useState<string | null>(null);
  const [paramError, setParamError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);

  const catsQuery = useMachineCategoriesQuery(catPage, catSearch.trim() || undefined);
  const machinesQuery = useMachinesQuery(machinePage, machineSearch.trim() || undefined);
  const allMachinesQuery = useMachinesQuery(1);
  const paramsQuery = useMachineParametersQuery(
    paramPage,
    selectedMachineId || undefined,
    paramSearch.trim() || undefined,
  );
  const imagesQuery = useMachineImagesQuery(
    imagePage,
    selectedMachineId || undefined,
    imageSearch.trim() || undefined,
  );

  const createCat = useCreateMachineCategoryMutation();
  const updateCat = useUpdateMachineCategoryMutation();
  const deleteCat = useDeleteMachineCategoryMutation();
  const createMachine = useCreateMachineMutation();
  const updateMachine = useUpdateMachineMutation();
  const deleteMachine = useDeleteMachineMutation();
  const createParam = useCreateMachineParameterMutation();
  const updateParam = useUpdateMachineParameterMutation();
  const deleteParam = useDeleteMachineParameterMutation();
  const createImage = useCreateMachineImageMutation();
  const updateImage = useUpdateMachineImageMutation();
  const deleteImage = useDeleteMachineImageMutation();

  const catData = (catsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const machineData =
    (machinesQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const allMachineItems = useMemo(
    () => (allMachinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [],
    [allMachinesQuery.data],
  );
  const paramData = (paramsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const imageData = (imagesQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const categoryLabelById = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of catData.items ?? []) {
      map.set(String(row.id ?? ""), String(row.name ?? ""));
    }
    return map;
  }, [catData.items]);

  const categoryOptions = useMemo(
    () =>
      (catData.items ?? []).map((row) => ({
        value: String(row.id ?? ""),
        label: `${String(row.code ?? "")} · ${String(row.name ?? "")}`,
      })),
    [catData.items],
  );

  const machineSelectOptions = useMemo(
    () =>
      allMachineItems.map((row) => ({
        value: String(row.id ?? ""),
        label: `${String(row.code ?? row.machine_code ?? "")} · ${String(row.name ?? "")}`,
      })),
    [allMachineItems],
  );

  const selectedMachineLabel =
    machineSelectOptions.find((opt) => opt.value === selectedMachineId)?.label ?? "";

  const catRows = useMemo(
    () =>
      (catData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        code: String(row.code ?? ""),
        name: String(row.name ?? ""),
        description: String(row.description ?? ""),
      })),
    [catData.items],
  );

  const machineRows = useMemo(
    () =>
      (machineData.items ?? []).map((row) => {
        const categoryId = String(row.category_id ?? "");
        const status = String(row.status ?? "");
        return {
          id: String(row.id ?? ""),
          code: String(row.code ?? row.machine_code ?? ""),
          name: String(row.name ?? ""),
          modelNo: String(row.model_no ?? ""),
          status,
          statusLabel: STATUS_LABEL[status] ?? status,
          categoryId,
          categoryLabel: categoryLabelById.get(categoryId) ?? "—",
          description: String(row.description ?? ""),
        };
      }),
    [machineData.items, categoryLabelById],
  );

  const paramRows = useMemo(
    () =>
      (paramData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        paramKey: String(row.param_key ?? ""),
        paramName: String(row.param_name ?? ""),
        value: String(row.value ?? ""),
        unit: String(row.unit ?? ""),
        remarks: String(row.remarks ?? ""),
      })),
    [paramData.items],
  );

  const imageRows = useMemo(
    () =>
      (imageData.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        fileUrl: String(row.file_url ?? ""),
        fileName: String(row.file_name ?? ""),
        sortOrder: String(row.sort_order ?? "0"),
      })),
    [imageData.items],
  );

  const closeAllForms = () => {
    setShowCatForm(false);
    setShowMachineForm(false);
    setShowParamForm(false);
    setShowImageForm(false);
    setCatEditId(null);
    setMachineEditId(null);
    setParamEditId(null);
    setImageEditId(null);
    setCatError(null);
    setMachineError(null);
    setParamError(null);
    setImageError(null);
  };

  const openCreateCat = () => {
    closeAllForms();
    setCatForm(emptyCategoryForm);
    setShowCatForm(true);
  };

  const openEditCat = (row: CategoryRow) => {
    closeAllForms();
    setCatEditId(row.id);
    setCatForm({ code: row.code, name: row.name, description: row.description });
    setShowCatForm(true);
  };

  const openCreateMachine = () => {
    closeAllForms();
    setMachineForm(emptyMachineForm);
    setShowMachineForm(true);
  };

  const openEditMachine = (row: MachineRow) => {
    closeAllForms();
    setMachineEditId(row.id);
    setMachineForm({
      category_id: row.categoryId,
      code: row.code,
      name: row.name,
      model_no: row.modelNo,
      status: row.status || "draft",
      description: row.description,
    });
    setShowMachineForm(true);
  };

  const openCreateParam = () => {
    if (!selectedMachineId) {
      notify("请先选择机型");
      return;
    }
    closeAllForms();
    setParamForm(emptyParamForm);
    setShowParamForm(true);
  };

  const openEditParam = (row: ParamRow) => {
    closeAllForms();
    setParamEditId(row.id);
    setParamForm({
      param_key: row.paramKey,
      param_name: row.paramName,
      value: row.value,
      unit: row.unit,
      remarks: row.remarks,
    });
    setShowParamForm(true);
  };

  const openCreateImage = () => {
    if (!selectedMachineId) {
      notify("请先选择机型");
      return;
    }
    closeAllForms();
    setImageForm(emptyImageForm);
    setShowImageForm(true);
  };

  const openEditImage = (row: ImageRow) => {
    closeAllForms();
    setImageEditId(row.id);
    setImageForm({
      file_url: row.fileUrl,
      file_name: row.fileName,
      sort_order: row.sortOrder,
    });
    setShowImageForm(true);
  };

  const handleSaveCat = async () => {
    setCatError(null);
    if (!catForm.code.trim() || !catForm.name.trim()) {
      setCatError("请填写分类编码和名称");
      return;
    }
    const body = {
      code: catForm.code.trim().toUpperCase(),
      name: catForm.name.trim(),
      description: catForm.description.trim() || undefined,
    };
    try {
      if (catEditId) await updateCat.mutateAsync({ id: catEditId, body });
      else await createCat.mutateAsync(body);
      setShowCatForm(false);
      setCatEditId(null);
      void catsQuery.refetch();
    } catch (err) {
      setCatError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteCat = async (id: string, label: string) => {
    if (!window.confirm(`确认删除机型分类「${label}」？`)) return;
    try {
      await deleteCat.mutateAsync(id);
      if (catEditId === id) closeAllForms();
      void catsQuery.refetch();
    } catch (err) {
      notify(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleSaveMachine = async () => {
    setMachineError(null);
    if (!machineForm.code.trim() || !machineForm.name.trim()) {
      setMachineError("请填写机型编码和名称");
      return;
    }
    const body = {
      category_id: machineForm.category_id.trim() || undefined,
      code: machineForm.code.trim(),
      name: machineForm.name.trim(),
      model_no: machineForm.model_no.trim() || undefined,
      status: machineForm.status || "draft",
      description: machineForm.description.trim() || undefined,
    };
    try {
      if (machineEditId) await updateMachine.mutateAsync({ id: machineEditId, body });
      else await createMachine.mutateAsync(body);
      setShowMachineForm(false);
      setMachineEditId(null);
      void machinesQuery.refetch();
      void allMachinesQuery.refetch();
    } catch (err) {
      setMachineError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteMachine = async (id: string, label: string) => {
    if (!window.confirm(`确认删除机型「${label}」？`)) return;
    try {
      await deleteMachine.mutateAsync(id);
      if (machineEditId === id) closeAllForms();
      if (selectedMachineId === id) setSelectedMachineId("");
      void machinesQuery.refetch();
      void allMachinesQuery.refetch();
    } catch (err) {
      notify(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleSaveParam = async () => {
    setParamError(null);
    if (!selectedMachineId) {
      setParamError("请先选择机型");
      return;
    }
    if (!paramForm.param_key.trim() || !paramForm.param_name.trim()) {
      setParamError("请填写参数键和参数名称");
      return;
    }
    const body = {
      param_key: paramForm.param_key.trim(),
      param_name: paramForm.param_name.trim(),
      value: paramForm.value.trim() || undefined,
      unit: paramForm.unit.trim() || undefined,
      remarks: paramForm.remarks.trim() || undefined,
    };
    try {
      if (paramEditId) await updateParam.mutateAsync({ id: paramEditId, body });
      else await createParam.mutateAsync({ machine_id: selectedMachineId, ...body });
      setShowParamForm(false);
      setParamEditId(null);
      void paramsQuery.refetch();
    } catch (err) {
      setParamError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteParam = async (id: string, label: string) => {
    if (!window.confirm(`确认删除参数「${label}」？`)) return;
    try {
      await deleteParam.mutateAsync(id);
      if (paramEditId === id) closeAllForms();
      void paramsQuery.refetch();
    } catch (err) {
      notify(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleSaveImage = async () => {
    setImageError(null);
    if (!selectedMachineId) {
      setImageError("请先选择机型");
      return;
    }
    if (!imageForm.file_url.trim()) {
      setImageError("请填写图片 URL");
      return;
    }
    const sortOrder = Number.parseInt(imageForm.sort_order, 10);
    const body = {
      file_url: imageForm.file_url.trim(),
      file_name: imageForm.file_name.trim() || undefined,
      sort_order: Number.isFinite(sortOrder) ? sortOrder : 0,
    };
    try {
      if (imageEditId) await updateImage.mutateAsync({ id: imageEditId, body });
      else await createImage.mutateAsync({ machine_id: selectedMachineId, ...body });
      setShowImageForm(false);
      setImageEditId(null);
      void imagesQuery.refetch();
    } catch (err) {
      setImageError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleDeleteImage = async (id: string, label: string) => {
    if (!window.confirm(`确认删除图片「${label || id}」？`)) return;
    try {
      await deleteImage.mutateAsync(id);
      if (imageEditId === id) closeAllForms();
      void imagesQuery.refetch();
    } catch (err) {
      notify(err instanceof Error ? err.message : "删除失败");
    }
  };

  return (
    <IndustrialPage gap="md" fill>
      {showCatForm ? (
        <MasterCreateForm
          title={catEditId ? "修改机型分类" : "新增机型分类"}
          fields={[
            { key: "code", label: "分类编码", required: true, placeholder: "如 INJ" },
            { key: "name", label: "分类名称", required: true, placeholder: "如 注塑机" },
            { key: "description", label: "描述" },
          ]}
          values={catForm}
          onChange={(key, value) => setCatForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveCat()}
          onCancel={closeAllForms}
          submitting={createCat.isPending || updateCat.isPending}
          error={catError}
          submitLabel={catEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {showMachineForm ? (
        <MasterCreateForm
          title={machineEditId ? "修改机型" : "新增机型"}
          fields={[
            {
              key: "category_id",
              label: "所属分类",
              type: "select",
              options: categoryOptions,
            },
            { key: "code", label: "机型编码", required: true, placeholder: "如 INJ-280T" },
            { key: "name", label: "机型名称", required: true, placeholder: "如 280T 注塑机" },
            { key: "model_no", label: "设备型号", placeholder: "如 ZH-280A" },
            { key: "status", label: "状态", type: "select", options: STATUS_OPTIONS },
            { key: "description", label: "描述" },
          ]}
          values={machineForm}
          onChange={(key, value) => setMachineForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveMachine()}
          onCancel={closeAllForms}
          submitting={createMachine.isPending || updateMachine.isPending}
          error={machineError}
          submitLabel={machineEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {showParamForm ? (
        <MasterCreateForm
          title={paramEditId ? "修改机型参数" : "新增机型参数"}
          fields={[
            {
              key: "param_key",
              label: "参数键",
              required: true,
              placeholder: "如 spec / power_kw / reference_price",
            },
            { key: "param_name", label: "参数名称", required: true, placeholder: "如 规格 / 功率 / 参考价" },
            { key: "value", label: "参数值", placeholder: "如 280T / 132 / 128000" },
            { key: "unit", label: "单位", placeholder: "如 kW / 元" },
            { key: "remarks", label: "备注" },
          ]}
          values={paramForm}
          onChange={(key, value) => setParamForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveParam()}
          onCancel={closeAllForms}
          submitting={createParam.isPending || updateParam.isPending}
          error={paramError}
          submitLabel={paramEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {showImageForm ? (
        <MasterCreateForm
          title={imageEditId ? "修改机型图片" : "新增机型图片"}
          fields={[
            { key: "file_url", label: "图片 URL", required: true, placeholder: "https://..." },
            { key: "file_name", label: "文件名", placeholder: "如 front-view.jpg" },
            { key: "sort_order", label: "排序", type: "number", placeholder: "0" },
          ]}
          values={imageForm}
          onChange={(key, value) => setImageForm((s) => ({ ...s, [key]: value }))}
          onSubmit={() => void handleSaveImage()}
          onCancel={closeAllForms}
          submitting={createImage.isPending || updateImage.isPending}
          error={imageError}
          submitLabel={imageEditId ? "保存修改" : "保存"}
        />
      ) : null}

      <MasterListPage<CategoryRow>
        embedded
        fill
        title="机型分类"
        persistenceKey="master-machine-categories-v1"
        exportFilename="machine-categories"
        columns={[
          { key: "code", title: "编码", canView: true, fixed: "left", width: 100 },
          { key: "name", title: "名称", canView: true, width: 140 },
          { key: "description", title: "描述", canView: true },
        ]}
        rows={catRows}
        total={catData.total ?? catRows.length}
        page={catPage}
        onPageChange={setCatPage}
        search={catSearch}
        onSearchChange={setCatSearch}
        query={catsQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <RowActions onEdit={() => openEditCat(row)} onDelete={() => void handleDeleteCat(row.id, row.name)} />
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreateCat}>新增分类</WorkspaceToolbarButton>}
        emptyHint="维护注塑机、压铸机等机型分类，供机型建档时选用"
      />

      <MasterListPage<MachineRow>
        embedded
        fill
        title="机型列表"
        persistenceKey="master-machines-v1"
        exportFilename="machines"
        columns={[
          { key: "code", title: "机型编码", canView: true, fixed: "left", width: 140 },
          { key: "name", title: "机型名称", canView: true, width: 180 },
          { key: "categoryLabel", title: "分类", canView: true, width: 120 },
          { key: "modelNo", title: "设备型号", canView: true },
          { key: "statusLabel", title: "状态", canView: true, width: 80 },
        ]}
        rows={machineRows}
        total={machineData.total ?? machineRows.length}
        page={machinePage}
        onPageChange={setMachinePage}
        search={machineSearch}
        onSearchChange={setMachineSearch}
        query={machinesQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <RowActions
            onEdit={() => openEditMachine(row)}
            onDelete={() => void handleDeleteMachine(row.id, row.name)}
            extra={
              <button
                type="button"
                className="text-xs text-emerald-400 hover:underline"
                onClick={() => setSelectedMachineId(row.id)}
              >
                参数
              </button>
            }
          />
        )}
        toolbarExtra={<WorkspaceToolbarButton onClick={openCreateMachine}>新增机型</WorkspaceToolbarButton>}
        emptyHint="标准机型名称、规格、功率与参考价在此维护，报价单可从此选用"
      />

      <MasterListPage<ParamRow>
        embedded
        fill
        title="机型参数"
        persistenceKey="master-machine-parameters-v1"
        exportFilename="machine-parameters"
        columns={[
          { key: "paramName", title: "参数名称", canView: true, fixed: "left", width: 120 },
          { key: "paramKey", title: "参数键", canView: true, width: 120 },
          { key: "value", title: "参数值", canView: true },
          { key: "unit", title: "单位", canView: true, width: 80 },
        ]}
        rows={paramRows}
        total={paramData.total ?? paramRows.length}
        page={paramPage}
        onPageChange={setParamPage}
        search={paramSearch}
        onSearchChange={setParamSearch}
        query={paramsQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <RowActions onEdit={() => openEditParam(row)} onDelete={() => void handleDeleteParam(row.id, row.paramName)} />
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <MachineSelect value={selectedMachineId} onChange={setSelectedMachineId} options={machineSelectOptions} />
            <WorkspaceToolbarButton onClick={openCreateParam} disabled={!selectedMachineId}>
              新增参数
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={
          selectedMachineId
            ? `当前机型：${selectedMachineLabel}。建议维护 spec（规格）、power_kw（功率）、reference_price（参考价）`
            : "请先在上方选择机型，或点击机型行的「参数」按钮"
        }
      />

      <MasterListPage<ImageRow>
        embedded
        fill
        title="机型图片"
        persistenceKey="master-machine-images-v1"
        exportFilename="machine-images"
        columns={[
          { key: "fileName", title: "文件名", canView: true, fixed: "left", width: 160 },
          { key: "fileUrl", title: "图片 URL", canView: true },
          { key: "sortOrder", title: "排序", canView: true, width: 60 },
        ]}
        rows={imageRows}
        total={imageData.total ?? imageRows.length}
        page={imagePage}
        onPageChange={setImagePage}
        search={imageSearch}
        onSearchChange={setImageSearch}
        query={imagesQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <RowActions
            onEdit={() => openEditImage(row)}
            onDelete={() => void handleDeleteImage(row.id, row.fileName || row.fileUrl)}
          />
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <MachineSelect value={selectedMachineId} onChange={setSelectedMachineId} options={machineSelectOptions} />
            <WorkspaceToolbarButton onClick={openCreateImage} disabled={!selectedMachineId}>
              新增图片
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={
          selectedMachineId
            ? `当前机型：${selectedMachineLabel}。录入图片 URL 即可引用（文件上传后续支持）`
            : "请先选择机型后再维护图片"
        }
      />

      <OptionGroupsSection machineOptions={machineSelectOptions} />
    </IndustrialPage>
  );
}

function notify(title: string) {
  useToastStore.getState().push({ title });
}
