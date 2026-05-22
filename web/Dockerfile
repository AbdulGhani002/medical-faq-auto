# Frontend image: Next.js 15 in standalone output mode.
#
# Three stages:
#   1. ``deps``  install npm deps (lockfile-aware)
#   2. ``build`` produce the ``.next/standalone`` bundle
#   3. ``run``   tiny final image — node + built assets only
#
# Build-time ``NEXT_PUBLIC_API_URL`` is hard-coded into the bundle.
# Default points at the ``api`` service on the compose network so the
# whole stack just works after ``docker compose up``.

FROM node:20-alpine AS deps
WORKDIR /app
RUN apk add --no-cache libc6-compat

COPY web/package.json web/package-lock.json* ./
RUN npm install --no-audit --no-fund

# -------------------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app
RUN apk add --no-cache libc6-compat
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY web/ ./

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# -------------------------------------------------------------------
FROM node:20-alpine AS run
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Non-root runtime user (Next.js standalone is fine with this).
RUN addgroup --system --gid 1001 nextjs \
    && adduser  --system --uid 1001 nextjs

COPY --from=build --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nextjs /app/public ./public

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=4 \
    CMD wget -q --spider --tries=1 http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
