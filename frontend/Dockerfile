# --- dev stage ---
FROM node:20-bookworm AS dev
WORKDIR /app
COPY package*.json /app/
RUN npm ci || npm install
COPY . /app
EXPOSE 3000
CMD ["bash", "-lc", "npm run dev -- --host 0.0.0.0 --port 3000"]

# --- build stage ---
FROM node:20-bookworm AS build
WORKDIR /app
COPY package*.json /app/
RUN npm ci || npm install
COPY . /app
RUN npm run build

# --- prod stage (static hosting) ---
FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
