import type { SearchResponse } from "../api/types";
import { fetchToolOrder } from "../api/client";

declare global {
  interface Window {
    ZeusTraceConfig?: Record<string, unknown>;
    appendTraceCard?: (query: string, data: unknown) => void;
    openDebugPanel?: () => void;
  }
}

let toolOrderInjected = false;

/** Cache-bust vendored widget so rebuilds replace browser cache. */
const TRACE_SCRIPT_SRC = `/static/zeus_client_chat_trace.js?v=${encodeURIComponent(
  import.meta.env.VITE_TRACE_WIDGET_VERSION || import.meta.env.VITE_APP_VERSION || "0.1.2"
)}`;

const DEFAULT_HUB_BASE_URL =
  (import.meta.env.VITE_HUB_BASE_URL as string | undefined) ||
  // Public demo front: Hub is path-routed at /zeus/. Local dev can still override via env.
  (typeof window !== "undefined" ? `${window.location.origin}/zeus` : "http://zeus-dev.local:9091");

/**
 * Widget (zeus_client_chat_trace.js) defaults zeusApiUrl to http://localhost:8080.
 * On a remote demo that produces CORS noise and failed /api/tool-order fetches.
 * Point it at same-origin so tool-order hits LocalAI nginx → /api/tool-order.
 */
function defaultZeusApiUrl(): string {
  const fromEnv = import.meta.env.VITE_ZEUS_API_URL as string | undefined;
  if (fromEnv && fromEnv.trim()) return fromEnv.replace(/\/$/, "");
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin;
  }
  return "";
}

function applyTraceConfig(partial: Record<string, unknown>) {
  window.ZeusTraceConfig = {
    ...(window.ZeusTraceConfig || {}),
    zeusApiUrl:
      (window.ZeusTraceConfig as { zeusApiUrl?: string })?.zeusApiUrl || defaultZeusApiUrl(),
    hubBaseUrl:
      (window.ZeusTraceConfig as { hubBaseUrl?: string })?.hubBaseUrl || DEFAULT_HUB_BASE_URL,
    ...partial,
  };
}

export function ensureTraceScript() {
  if (typeof window === "undefined") return;
  if (!window.ZeusTraceConfig) window.ZeusTraceConfig = {};

  // Set same-origin Zeus API + Hub base *before* the widget script runs (avoids
  // localhost:8080 default and race with async tool-order).
  applyTraceConfig({});

  if (!toolOrderInjected) {
    toolOrderInjected = true;
    // Background; never gate UI
    fetchToolOrder()
      .then((order) => {
        applyTraceConfig({ toolOrder: order });
      })
      .catch(() => {
        /* ignore */
      });
  }

  if (document.getElementById("zeus-trace-script")) return;
  const s = document.createElement("script");
  s.id = "zeus-trace-script";
  s.src = TRACE_SCRIPT_SRC;
  s.async = true;
  document.body.appendChild(s);
}

export function appendTrace(query: string, data: SearchResponse) {
  ensureTraceScript();
  if (typeof window.appendTraceCard === "function") {
    window.appendTraceCard(query, data);
  }
}
