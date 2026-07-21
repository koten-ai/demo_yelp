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

export function ensureTraceScript() {
  if (typeof window === "undefined") return;
  if (!window.ZeusTraceConfig) window.ZeusTraceConfig = {};

  if (!toolOrderInjected) {
    toolOrderInjected = true;
    // Background; never gate UI
    fetchToolOrder()
      .then((order) => {
        window.ZeusTraceConfig = {
          ...(window.ZeusTraceConfig || {}),
          toolOrder: order,
        };
      })
      .catch(() => {
        /* ignore */
      });
  }

  if (document.getElementById("zeus-trace-script")) return;
  const s = document.createElement("script");
  s.id = "zeus-trace-script";
  s.src = "/static/zeus_client_chat_trace.js";
  s.async = true;
  document.body.appendChild(s);
}

export function appendTrace(query: string, data: SearchResponse) {
  ensureTraceScript();
  if (typeof window.appendTraceCard === "function") {
    window.appendTraceCard(query, data);
  }
}
