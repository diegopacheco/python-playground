import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { startAnalytics } from "./analytics/posthog";
import { App } from "./App";
import "./styles.css";

startAnalytics();

const container = document.getElementById("root");
if (!container) throw new Error("missing #root element");

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
