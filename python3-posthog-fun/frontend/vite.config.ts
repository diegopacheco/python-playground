import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const here = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, resolve(here, ".."), "");
  const apiTarget = process.env.API_URL ?? "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    define: {
      __POSTHOG_KEY__: JSON.stringify(env.POSTHOG_PROJECT_TOKEN ?? ""),
      __POSTHOG_HOST__: JSON.stringify(env.POSTHOG_HOST ?? ""),
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
