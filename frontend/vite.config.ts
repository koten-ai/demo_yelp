import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const pkg = JSON.parse(
  readFileSync(new URL("./package.json", import.meta.url), "utf-8"),
) as { version: string };

// In Docker Compose the API is another service; locally it is loopback :5000.
const apiProxy = process.env.VITE_API_PROXY || "http://127.0.0.1:5000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Bind-mounts on Linux Docker often miss inotify; polling keeps HMR reliable.
    watch: {
      usePolling: process.env.VITE_USE_POLLING === "1",
    },
    proxy: {
      "/api": apiProxy,
      "/static": apiProxy,
    },
    allowedHosts: ["zeus-dev.local", "localhost", ".localhost"],
  },
});
