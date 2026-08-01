import { MotionConfig } from "framer-motion";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Self-hosted fonts (docs/FRONTEND.md §3.2), only the weights/axes used:
// Fraunces variable (opsz + wght + WONK) for display, Instrument Sans 400/500/
// 600 for UI, JetBrains Mono variable for data.
import "@fontsource-variable/fraunces/full.css";
import "@fontsource/instrument-sans/400.css";
import "@fontsource/instrument-sans/500.css";
import "@fontsource/instrument-sans/600.css";
import "@fontsource-variable/jetbrains-mono/wght.css";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* Single, app-wide reduced-motion honouring (docs/FRONTEND.md §7). */}
    <MotionConfig reducedMotion="user">
      <App />
    </MotionConfig>
  </StrictMode>,
);
