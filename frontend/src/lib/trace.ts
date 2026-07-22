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
  import.meta.env.VITE_TRACE_WIDGET_VERSION || import.meta.env.VITE_APP_VERSION || "0.1.0"
)}`;

const DEFAULT_HUB_BASE_URL =
  (import.meta.env.VITE_HUB_BASE_URL as string | undefined) || "http://zeus-dev.local:9091";

export function ensureTraceScript() {
  if (typeof window === "undefined") return;
  if (!window.ZeusTraceConfig) window.ZeusTraceConfig = {};

  // Hub base must be present before first appendTraceCard (not only after tool-order).
  window.ZeusTraceConfig = {
    ...(window.ZeusTraceConfig || {}),
    hubBaseUrl:
      (window.ZeusTraceConfig as { hubBaseUrl?: string }).hubBaseUrl || DEFAULT_HUB_BASE_URL,
  };

  if (!toolOrderInjected) {
    toolOrderInjected = true;
    // Background; never gate UI
    fetchToolOrder()
      .then((order) => {
        window.ZeusTraceConfig = {
          ...(window.ZeusTraceConfig || {}),
          toolOrder: order,
          hubBaseUrl:
            (window.ZeusTraceConfig as { hubBaseUrl?: string })?.hubBaseUrl || DEFAULT_HUB_BASE_URL,
        };
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
