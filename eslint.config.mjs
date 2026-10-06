// Root config: the app keeps its own (nearest config wins for its files), and this covers the
// packages, which had no lint coverage at all. Presets are imported by path into the app's
// node_modules because that is where they live; Node resolves their dependencies from that location.
// `eslint/config` is deliberately not imported — eslint is not installed at the root, so importing it
// would fail here.
import nextVitals from "./apps/web-admin/node_modules/eslint-config-next/dist/core-web-vitals.js";
import nextTs from "./apps/web-admin/node_modules/eslint-config-next/dist/typescript.js";

export default [
  ...nextVitals,
  ...nextTs,
  {
    files: ["packages/*/src/**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
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
          ],
        },
      ],
    },
  },
  {
    ignores: [
      "**/node_modules/**",
      "**/.next/**",
      "**/out/**",
      "**/build/**",
      "**/dist/**",
      "**/coverage/**",
    ],
  },
];
