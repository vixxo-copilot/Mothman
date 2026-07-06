#!/usr/bin/env bash
# Reset Gateway MCP OAuth cache and start a fresh login (mcp-remote-client, port 3334).
# Complete sign-in in the cloud-agent browser so localhost:3334 callback succeeds.
set -euo pipefail

GATEWAY_URL="https://vixxonow.com/mcp/gateway"
CALLBACK_PORT="3334"
LOG="/tmp/gateway-oauth-client.log"
OUT="/tmp/gateway-oauth-client.out"
SESSION="gateway-oauth-client"

echo "Stopping stale mcp-remote processes..."
pkill -f 'mcp-remote.*gateway' 2>/dev/null || true
pkill -f 'x-www-browser.*gateway/oauth' 2>/dev/null || true

echo "Clearing ~/.mcp-auth ..."
rm -rf "${HOME}/.mcp-auth"/*
: > "${LOG}"
: > "${OUT}"

echo "Starting mcp-remote-client (callback http://127.0.0.1:${CALLBACK_PORT})..."
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "=${SESSION}" 2>/dev/null || true
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "${SESSION}" -c "$(dirname "$0")/../.." -- "${SHELL:-bash}" -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "${SESSION}:0.0" \
  "npx -y -p mcp-remote@latest mcp-remote-client ${GATEWAY_URL} ${CALLBACK_PORT} --debug --auth-timeout 600 2>${LOG} | tee ${OUT}" C-m

echo "Waiting for authorize URL..."
for _ in $(seq 1 30); do
  AUTH_URL=$(rg --no-filename -o 'https://vixxonow.com/mcp/gateway/oauth/authorize[^ ]+' "${LOG}" "${OUT}" 2>/dev/null | tail -1 || true)
  if [[ -n "${AUTH_URL}" ]]; then
  echo ""
  echo "Open this URL in the cloud-agent browser (NOT your local desktop):"
  echo "${AUTH_URL}"
  x-www-browser "${AUTH_URL}" >/dev/null 2>&1 &
  echo "Browser launched. After login, tokens land in ~/.mcp-auth/*_tokens.json"
  exit 0
  fi
  sleep 1
done

echo "Authorize URL not ready yet. Check: tail -f ${LOG}" >&2
exit 1
