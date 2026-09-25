#!/usr/bin/env bash
# Obsolete: demo_yelp loads Zeus chat-trace from the public CDN, not a vendored copy.
#   https://koten-static-cdn.nyc3.cdn.digitaloceanspaces.com/zeus_client_chat_trace/latest/zeus_client_chat_trace.js
#
# Publish a new bundle from the chat-trace repo:
#   cd ../zeus_client_chat_trace && npm test && npm run build && npm run publish:cdn
#
# Optional frontend overrides (Vite):
#   VITE_TRACE_SCRIPT_SRC=https://…/zeus_client_chat_trace/<semver>/zeus_client_chat_trace.js
#   VITE_TRACE_WIDGET_VERSION=0.1.x   # appends ?v= when using latest
set -euo pipefail
echo "demo_yelp no longer vendors zeus_client_chat_trace.js — use CDN (see script header)." >&2
exit 1
