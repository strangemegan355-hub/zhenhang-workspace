import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm, type FieldValues, type Resolver } from "react-hook-form";
import { z } from "zod";

export type FieldConfig = {
  name: string;
  label: string;
  type?: "text" | "number" | "select";
  options?: Array<{ label: string; value: string }>;
  visible?: (state: { workflowState?: string }) => boolean;
};

// Not generic on the schema type on purpose. zod infers a schema's output separately from the generic
// that carries it, while react-hook-form requires its `FieldValues` constraint, so every formulation of
// `T extends z.ZodType<…>` produced a different type error here. The component has no callers, so
// correctness with `FieldValues` — and a caller-side narrowing if one is ever needed — beats a
// constraint that cannot be satisfied. See round 47 in the hardening skill.
type Props = {
  schema: z.ZodType<FieldValues>;
  fields: FieldConfig[];
  workflowState?: string;
  defaultValues: FieldValues;
  onSubmit: (value: FieldValues) => void;
};

export function SchemaFormEngine({ schema, fields, workflowState, defaultValues, onSubmit }: Props) {
  const form = useForm<FieldValues>({
    // `@hookform/resolvers` types zodResolver against zod v3 while the installed zod exports v4-shaped
    // types, so the overload cannot resolve; the argument is cast rather than the result, because the
    // error is reported at the call.
    resolver: zodResolver(schema as never) as Resolver<FieldValues>,
    defaultValues,
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
