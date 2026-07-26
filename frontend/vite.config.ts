import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    // Docker (WSL2 + Windows host dosya sistemi) üzerinde inotify olayları bind mount'a
    // yansımayabiliyor - dosya değişikliklerini yakalamak için polling'e zorla.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
});
