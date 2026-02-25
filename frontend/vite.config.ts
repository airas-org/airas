import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  envDir: path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(path.dirname(fileURLToPath(import.meta.url)), "./src"),
    },
  },
});
