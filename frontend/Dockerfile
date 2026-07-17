# --- build stage ---
FROM node:22-bookworm AS build
WORKDIR /app
# pnpm via corepack: the version follows package.json's packageManager field
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml /app/
RUN pnpm install --frozen-lockfile
COPY . /app
RUN pnpm run build

# --- prod stage (static hosting) ---
FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
