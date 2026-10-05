"use client";

import { WorkspaceToolbarButton, typography } from "@zhenhang/ui";
import {
  dangerActionClass,
  fieldInputClass,
  fieldLabelClass,
  formPanelClass,
} from "@/lib/form-styles";

type Field = {
  key: string;
  label: string;
  type?: "text" | "number" | "select" | "checkbox";
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  required?: boolean;
};

export function MasterCreateForm({
  title,
  fields,
  values,
  onChange,
  onSubmit,
  onCancel,
  submitting,
  error,
  submitLabel = "保存",
}: {
  title: string;
  fields: Field[];
  values: Record<string, string | boolean>;
  onChange: (key: string, value: string | boolean) => void;
  onSubmit: () => void;
  onCancel: () => void;
  submitting?: boolean;
  error?: string | null;
  submitLabel?: string;
}) {
  return (
    <div className={formPanelClass}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className={typography.sectionTitle}>{title}</h3>
        <WorkspaceToolbarButton onClick={onCancel}>取消</WorkspaceToolbarButton>
      </div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {fields.map((field) => (
          <label key={field.key} className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>
              {field.label}
              {field.required ? " *" : ""}
            </span>
            {field.type === "select" ? (
              <select
                className={fieldInputClass}
                value={String(values[field.key] ?? "")}
                onChange={(e) => onChange(field.key, e.target.value)}
              >
                <option value="">请选择</option>
                {field.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : field.type === "checkbox" ? (
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={Boolean(values[field.key])}
                onChange={(e) => onChange(field.key, e.target.checked)}
              />
            ) : (
              <input
                type={field.type ?? "text"}
                className={fieldInputClass}
                placeholder={field.placeholder}
                value={String(values[field.key] ?? "")}
                onChange={(e) => onChange(field.key, e.target.value)}
              />
            )}
          </label>
        ))}
      </div>
      {error ? <p className={`mt-2 ${dangerActionClass}`}>{error}</p> : null}
      <div className="mt-3 flex justify-end">
        <button type="button" disabled={submitting} onClick={onSubmit} className="btn-primary h-8 px-4 text-xs">
          {submitting ? "保存中…" : submitLabel}
        </button>
      </div>
    </div>
  );
}
