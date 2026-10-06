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
    "@zhenhang/ai-ui",
    "@zhenhang/event-stream",
    "@zhenhang/formula-engine",
    "@zhenhang/runtime-bus",
    "@zhenhang/runtime-graph",
    "@zhenhang/formula-runtime",
    "@zhenhang/formula-dag",
  ],
  // Round 205: the admin app served HTML with no security headers at all — measured: nothing in this file and nothing
  // anywhere else in `apps/` or `packages/`. The backend authenticates with a **Bearer token in the response body**, not
  // a cookie, so CSRF protection is genuinely unnecessary here; the headers below are the ones that do not depend on how
  // the app is deployed beyond HTTPS.
  //
  // **A `Content-Security-Policy` is deliberately NOT set.** A restrictive policy that has not been exercised in a real
  // browser breaks whatever it was not tested against, and this session cannot run one — so the honest move is to leave
  // it out and say so, rather than to ship a header whose effect is unverified.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          // Stops a browser from re-interpreting a response as a type it was not served as.
          { key: "X-Content-Type-Options", value: "nosniff" },
          // The admin UI is never meant to be framed; this is the clickjacking control.
          { key: "X-Frame-Options", value: "DENY" },
          // Keep the full URL out of the `Referer` sent to other origins.
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // Only meaningful over HTTPS, and inert over plain HTTP, so it is safe to send unconditionally.
          { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
        ],
      },
    ];
  },
};

export default nextConfig;
