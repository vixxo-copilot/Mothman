#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_BIN="${SCRIPT_DIR}/github-mcp-server"

if [[ ! -x "${SERVER_BIN}" ]]; then
  echo "github-mcp-stdio: missing binary at ${SERVER_BIN}" >&2
  echo "Download v1.2.0 Darwin binary from https://github.com/github/github-mcp-server/releases" >&2
  exit 1
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  if command -v gh >/dev/null 2>&1; then
    GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null || true)"
    export GITHUB_PERSONAL_ACCESS_TOKEN
  fi
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  echo "github-mcp-stdio: set GITHUB_PERSONAL_ACCESS_TOKEN or run 'gh auth login'" >&2
  exit 1
fi

exec "${SERVER_BIN}" stdio "$@"
