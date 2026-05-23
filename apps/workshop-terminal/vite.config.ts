import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@zhenhang/http-client": path.resolve(__dirname, "../../packages/http-client/src/index.ts"),
      "@zhenhang/query-hooks": path.resolve(__dirname, "../../packages/query-hooks/src/index.ts"),
      "@zhenhang/query-policy-registry": path.resolve(
        __dirname,
        "../../packages/query-policy-registry/src/index.ts",
      ),
    },
  },
  server: { port: 5175 },
});
