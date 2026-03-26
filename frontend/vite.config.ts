import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  envDir: path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  define: {
    "import.meta.env.ENTERPRISE_ENABLED": JSON.stringify(process.env.ENTERPRISE_ENABLED ?? "false"),
  },
  plugins: [react()],
  server: {
    allowedHosts: [".trycloudflare.com"],
  },
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(fileURLToPath(import.meta.url)), "./src"),
    },
  },
});
