import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Read VITE_* vars from the repo-root .env (shared with the backend)
  // instead of requiring a second, duplicated frontend/.env.
  envDir: "../",
  test: {
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
