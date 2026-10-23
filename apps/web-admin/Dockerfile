FROM node:20-alpine AS builder
WORKDIR /app

# musl needs the matching optional native bindings for PostCSS/lightningcss.
RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json tsconfig.base.json tsconfig.packages.json ./
COPY apps ./apps
COPY packages ./packages

RUN npm ci \
  && npm install --no-save --no-package-lock \
    lightningcss-linux-x64-musl \
    @tailwindcss/oxide-linux-x64-musl \
  || true

ARG NEXT_PUBLIC_API_BASE_URL=
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build -w web-admin

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs \
  && apk add --no-cache curl libc6-compat

COPY --from=builder /app/apps/web-admin/public ./apps/web-admin/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web-admin/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web-admin/.next/static ./apps/web-admin/.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:3000/ || exit 1

CMD ["node", "apps/web-admin/server.js"]
