/**
 * `process.env` as the bundler provides it.
 *
 * `packages/http-client` reads `process.env.NEXT_PUBLIC_API_BASE_URL`, which Next declares through its
 * own ambient types for the app. A standalone `tsc -p tsconfig.packages.json` has no such declaration,
 * and this states the assumption rather than turning the check off.
 */
declare const process: { env: Record<string, string | undefined> };
