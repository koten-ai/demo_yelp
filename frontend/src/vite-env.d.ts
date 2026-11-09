/// <reference types="vite/client" />

interface Window {
  appendTraceCard?: (query: string, data: unknown) => void;
  openDebugPanel?: () => void;
}
