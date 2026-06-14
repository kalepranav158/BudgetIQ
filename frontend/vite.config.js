import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/django-api": {
        target: process.env.VITE_DJANGO_URL || "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/django-api/, "")
      },
      "/fastapi-api": {
        target: process.env.VITE_FASTAPI_URL || "http://127.0.0.1:8001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/fastapi-api/, "")
      }
    }
  }
});
