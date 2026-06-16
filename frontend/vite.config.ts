import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist"
  },
  server: {
    port: 5173,
    proxy: {
      "/process": "http://127.0.0.1:8000",
      "/process-url": "http://127.0.0.1:8000",
      "/submit": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/static": "http://127.0.0.1:8000"
    }
  }
});