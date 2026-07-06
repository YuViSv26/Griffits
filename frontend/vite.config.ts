import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  optimizeDeps: {
    include: ["html2canvas-pro"],
  },
  resolve: {
    alias: {
      html2canvas: "html2canvas-pro",
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY || "http://localhost:8080",
        changeOrigin: true,
      },
      "/health": {
        target: process.env.VITE_API_PROXY || "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
