import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      // A leading underscore marks a binding that exists only to be discarded, which is how the
      // code strips a field out of a payload before sending the rest ({ field: _field, ...rest }).
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      // Governance: app cannot bypass hooks by directly importing SDK internals.
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "@zhenhang/api-sdk",
              message: "Use @zhenhang/query-hooks as the only data entry for pages.",
            },
          ],
          patterns: [
            {
              group: ["@zhenhang/*/src/*"],
              message: "Do not import package internal source paths directly.",
            },
            {
              group: ["@zhenhang/business/*", "@zhenhang/platform/*", "@zhenhang/core/*"],
              message: "Use package public entry exports, not governance aliases.",
            },
          ],
        },
      ],
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
