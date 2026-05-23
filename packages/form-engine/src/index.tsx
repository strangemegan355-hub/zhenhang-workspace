import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

export type FieldConfig = {
  name: string;
  label: string;
  type?: "text" | "number" | "select";
  options?: Array<{ label: string; value: string }>;
  visible?: (state: { workflowState?: string }) => boolean;
};

type Props<T extends z.ZodType> = {
  schema: T;
  fields: FieldConfig[];
  workflowState?: string;
  defaultValues: Record<string, unknown>;
  onSubmit: (value: z.infer<T>) => void;
};

export function SchemaFormEngine<T extends z.ZodType>({
  schema,
  fields,
  workflowState,
  defaultValues,
  onSubmit,
}: Props<T>) {
  const form = useForm<z.infer<T>>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues as z.infer<T>,
  });
  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
      {fields
        .filter((f) => (f.visible ? f.visible({ workflowState }) : true))
        .map((f) => (
          <div key={f.name}>
            <label className="mb-1 block text-sm">{f.label}</label>
            {f.type === "select" ? (
              <select className="h-10 w-full rounded border px-2" {...form.register(f.name as never)}>
                {(f.options ?? []).map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input className="h-10 w-full rounded border px-3" {...form.register(f.name as never)} />
            )}
          </div>
        ))}
      <button className="h-10 rounded border px-4">Submit</button>
    </form>
  );
}
