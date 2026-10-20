# Production image only (dev keeps using `npm run dev`). Stage 1 builds the
# static site; stage 2 serves it with Caddy, which also terminates HTTPS and
# forwards /api/* to the backend — see Caddyfile and docker-compose.prod.yml.
FROM node:24-alpine AS build

WORKDIR /app

# Dependencies first, so this layer is cached until the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Same-origin API: the browser calls /api/..., Caddy strips the prefix and
# proxies to the backend. Baked in at build time (Vite inlines VITE_* vars).
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM caddy:2.10-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
