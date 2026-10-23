"use client";

import { WorkspaceToolbarButton, typography } from "@zhenhang/ui";
import {
  dangerActionClass,
  fieldInputClass,
  fieldLabelClass,
  formPanelClass,
} from "@/lib/form-styles";

export type MasterFormField = {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "select" | "checkbox" | "textarea";
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  required?: boolean;
  /** When true, control is not editable (e.g. customer filled from quote). */
  disabled?: boolean;
  hint?: string;
};

type Field = MasterFormField;

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
                disabled={field.disabled}
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
                disabled={field.disabled}
                onChange={(e) => onChange(field.key, e.target.checked)}
              />
            ) : field.type === "textarea" ? (
              <textarea
                className={`${fieldInputClass} min-h-[96px] font-mono`}
                placeholder={field.placeholder}
                value={String(values[field.key] ?? "")}
                disabled={field.disabled}
                onChange={(e) => onChange(field.key, e.target.value)}
              />
            ) : (
              <input
                type={field.type ?? "text"}
                className={fieldInputClass}
                placeholder={field.placeholder}
                value={String(values[field.key] ?? "")}
                disabled={field.disabled}
                onChange={(e) => onChange(field.key, e.target.value)}
              />
            )}
            {field.hint ? <span className="text-[10px] text-[var(--color-text-muted)]">{field.hint}</span> : null}
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
