#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TRACE_SRC="${TRACE_SRC:-$ROOT/../zeus_client_chat_trace}"
mkdir -p "$ROOT/src/local_guide/static"
if [[ -f "$TRACE_SRC/dist/zeus_client_chat_trace.js" ]]; then
  cp -f "$TRACE_SRC/dist/zeus_client_chat_trace.js" "$ROOT/src/local_guide/static/"
  cp -f "$TRACE_SRC/dist/zeus_client_chat_trace.js.map" "$ROOT/src/local_guide/static/" 2>/dev/null || true
elif [[ -f "$ROOT/../demo_travel_sample/src/travel_planner/static/zeus_client_chat_trace.js" ]]; then
  cp -f "$ROOT/../demo_travel_sample/src/travel_planner/static/zeus_client_chat_trace.js" "$ROOT/src/local_guide/static/"
  cp -f "$ROOT/../demo_travel_sample/src/travel_planner/static/zeus_client_chat_trace.js.map" "$ROOT/src/local_guide/static/" 2>/dev/null || true
else
  echo "No prebuilt trace bundle found; build zeus_client_chat_trace first" >&2
  exit 1
fi
echo "vendored → src/local_guide/static/"
