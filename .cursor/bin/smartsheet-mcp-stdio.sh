#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -z "${SMARTSHEET_API_TOKEN:-}" && -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

if [[ -z "${SMARTSHEET_API_TOKEN:-}" ]]; then
  echo "smartsheet-mcp-stdio: set SMARTSHEET_API_TOKEN in .env or environment" >&2
  exit 1
fi

exec npx -y mcp-remote "https://mcp.smartsheet.com" --header "Authorization:${SMARTSHEET_API_TOKEN}"
