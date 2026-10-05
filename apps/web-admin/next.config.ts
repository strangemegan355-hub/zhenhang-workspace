import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(rootDir, "../.."),
  transpilePackages: [
    "@zhenhang/ui",
    "@zhenhang/auth",
    "@zhenhang/api-sdk",
    "@zhenhang/http-client",
    "@zhenhang/query-hooks",
    "@zhenhang/data-grid",
    "@zhenhang/form-engine",
    "@zhenhang/workflow-ui",
    "@zhenhang/quote-builder",
    "@zhenhang/workflow-graph",
    "@zhenhang/realtime",
    "@zhenhang/realtime-gateway",
    "@zhenhang/realtime-protocol",
    "@zhenhang/query-policy-registry",
    "@zhenhang/workflow-runtime",
    "@zhenhang/quote-runtime",
    "@zhenhang/ai-command",
    "@zhenhang/ai-runtime",
    "@zhenhang/ai-ui",
    "@zhenhang/event-stream",
    "@zhenhang/formula-engine",
    "@zhenhang/runtime-devtools",
    "@zhenhang/runtime-telemetry",
    "@zhenhang/runtime-bus",
    "@zhenhang/runtime-graph",
    "@zhenhang/telemetry-pipeline",
    "@zhenhang/formula-runtime",
    "@zhenhang/agent-runtime",
    "@zhenhang/agent-os",
    "@zhenhang/distributed-runtime",
    "@zhenhang/formula-dag",
    "@zhenhang/runtime-persistence",
    "@zhenhang/runtime-scheduler",
    "@zhenhang/runtime-consistency",
    "@zhenhang/distributed-coordination",
    "@zhenhang/runtime-storage",
    "@zhenhang/agent-governance",
    "@zhenhang/runtime-security",
    "@zhenhang/runtime-transaction",
    "@zhenhang/consensus-coordination",
    "@zhenhang/runtime-event-store",
    "@zhenhang/agent-policy-engine",
    "@zhenhang/runtime-fault-tolerance",
  ],
};

export default nextConfig;
