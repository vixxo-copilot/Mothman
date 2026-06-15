#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

load_env_file() {
  local file="$1"
  [[ -f "${file}" ]] || return 0
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue
    [[ "${line}" =~ ^[[:space:]]*$ ]] && continue
    if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local val="${BASH_REMATCH[2]}"
      val="${val#\"}"; val="${val%\"}"
      val="${val#\'}"; val="${val%\'}"
      [[ -n "${val}" ]] || continue
      if [[ -z "${!key:-}" ]]; then
        export "${key}=${val}"
      fi
    fi
  done < "${file}"
}

load_secret_file() {
  local file="$1"
  local target_var="$2"
  [[ -f "${file}" ]] || return 0
  if [[ -z "${!target_var:-}" ]]; then
    local secret
    secret="$(tr -d '\r\n' < "${file}")"
    if [[ -n "${secret}" ]]; then
      export "${target_var}=${secret}"
    fi
  fi
}

load_env_file "${ROOT}/.env"
load_secret_file "${HOME}/.vixxo/freshservice_api_key" "FRESHSERVICE_API_KEY"
load_secret_file "${HOME}/.vixxo/freshservice_token" "FRESHSERVICE_API_KEY"

UVX=""
for candidate in \
  "${HOME}/Library/Python/"*/bin/uvx \
  "${HOME}/.local/bin/uvx" \
  "/opt/homebrew/bin/uvx" \
  "/usr/local/bin/uvx"; do
  if [[ -x "${candidate}" ]]; then
    UVX="${candidate}"
    break
  fi
done

if [[ -z "${UVX}" ]] && command -v uvx >/dev/null 2>&1; then
  UVX="$(command -v uvx)"
fi

if [[ -z "${UVX}" ]] && python3 -m uv --version >/dev/null 2>&1; then
  UVX="python3 -m uv tool run"
fi

if [[ -z "${UVX}" ]]; then
  echo "Freshservice MCP: uvx not found. Run: bin/setup-freshservice-mcp.sh" >&2
  exit 1
fi

export FRESHSERVICE_DOMAIN="${FRESHSERVICE_DOMAIN:-vixxo.freshservice.com}"

if [[ -z "${FRESHSERVICE_API_KEY:-}" && -n "${FRESHSERVICE_APIKEY:-}" ]]; then
  export FRESHSERVICE_API_KEY="${FRESHSERVICE_APIKEY}"
fi

if [[ -z "${FRESHSERVICE_API_KEY:-}" ]]; then
  echo "Freshservice MCP: FRESHSERVICE_API_KEY not set — server will start but API tools will fail until configured." >&2
  echo "Fix: run bin/setup-freshservice-mcp.sh, set .env or ~/.vixxo/freshservice_api_key, restart MCP." >&2
fi

if [[ "${UVX}" == "python3 -m uv tool run" ]]; then
  exec python3 -m uv tool run freshservice-mcp "$@"
fi

exec "${UVX}" freshservice-mcp "$@"
