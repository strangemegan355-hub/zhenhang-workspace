/** Package layer assignments for boundary checks. */
export const PACKAGE_LAYERS = {
  core: [
    "http-client",
    "query-governance",
    "query-policy-registry",
    "realtime-gateway",
    "realtime-protocol",
    "runtime-telemetry",
    "event-stream",
    "formula-engine",
    "runtime-bus",
    "runtime-scheduler",
    "runtime-persistence",
    "distributed-runtime",
    "runtime-consistency",
    "distributed-coordination",
    "runtime-storage",
    "runtime-security",
    "runtime-transaction",
    "consensus-coordination",
    "runtime-event-store",
    "runtime-fault-tolerance",
    "agent-policy-engine",
    "agent-governance",
    "telemetry-pipeline",
    "dependency-analyzer",
    "api-sdk",
  ],
  platform: [
    "query-hooks",
    "data-grid",
    "form-engine",
    "workflow-schema",
    "workflow-ui",
    "workflow-graph",
    "workflow-runtime",
    "runtime-devtools",
    "runtime-graph",
    "formula-runtime",
    "formula-dag",
    "realtime",
    "auth",
    "ui",
  ],
  business: [
    "quote-builder",
    "quote-runtime",
    "quote",
    "file-center",
    "ai-ui",
    "ai-command",
    "ai-runtime",
    "agent-runtime",
    "agent-os",
    "workflow",
  ],
};

/** Allowed dependency direction: layer -> can import from these layers. */
export const LAYER_ALLOWED_IMPORTS = {
  core: ["core"],
  platform: ["core", "platform"],
  business: ["core", "platform", "business"],
  apps: ["core", "platform", "business"],
};

/** Forbidden import patterns for apps and packages. */
export const FORBIDDEN_IMPORT_PATTERNS = [
  { pattern: /@zhenhang\/api-sdk/, message: "Use query-hooks as data entry; do not import api-sdk directly in apps." },
  { pattern: /\/src\//, message: "Do not import package internal /src/ paths." },
];
