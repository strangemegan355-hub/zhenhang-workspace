// The shared packages read `process.env`, which Vite substitutes at build time. This app has no
// Node type dependency and should not need one: declaring exactly what the shared code uses keeps
// the browser bundle type-checkable without pulling @types/node into it.
declare const process: {
  env: Record<string, string | undefined>;
};
