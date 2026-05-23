import { z } from "zod";

export const workflowActionSchema = z.object({
  code: z.string().min(1),
  label: z.string().min(1),
  next_state: z.string().min(1),
});

export const workflowPermissionSchema = z.object({
  action_code: z.string().min(1),
  permissions: z.array(z.string()).default([]),
});

export const workflowStateMetadataSchema = z.object({
  code: z.string().min(1),
  label: z.string().min(1),
  color: z.string().default("zinc"),
  terminal: z.boolean().default(false),
});

export const workflowSchema = z.object({
  workflow_code: z.string().min(1),
  states: z.array(workflowStateMetadataSchema),
  actions: z.array(workflowActionSchema),
  permissions: z.array(workflowPermissionSchema),
});

export type WorkflowSchema = z.infer<typeof workflowSchema>;

export function parseWorkflowSchema(input: unknown): WorkflowSchema {
  return workflowSchema.parse(input);
}
