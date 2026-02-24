import path from "path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 9000,
    proxy: {
      "/api": "http://localhost:8888",
      "/skill.md": "http://localhost:8888",
      "/heartbeat.md": "http://localhost:8888",
      "/skill.json": "http://localhost:8888",
      "/claim": "http://localhost:8888",
    },
  },
})
