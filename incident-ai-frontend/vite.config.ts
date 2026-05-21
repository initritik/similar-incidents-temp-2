import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Vite is used because it gives React teams fast local startup, quick hot
// module replacement, and a simple production build pipeline.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
