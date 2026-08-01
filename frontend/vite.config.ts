import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Read VITE_* vars from the repo-root .env (shared with the backend)
  // instead of requiring a second, duplicated frontend/.env.
  envDir: "../",
  server: {
    // Fail if 5173 is taken instead of silently moving to 5174+: the
    // backend's CORS allow-list is pinned to 5173, so a silent port switch
    // makes every request fail with a confusing, hard-to-diagnose CORS
    // rejection instead of an obvious "port already in use" error.
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
    include: ["tests/**/*.test.{ts,tsx}"],
    // The form tests drive many sequential userEvent keystrokes; under full
    // parallel load on a busy machine they can exceed the 5s default even
    // though they pass in isolation. Give them headroom so the suite is
    // deterministic in CI.
    testTimeout: 20000,
  },
});
