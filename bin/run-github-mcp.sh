#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${ROOT}/bin/github-mcp-server"

if [[ ! -x "${BIN}" ]]; then
  echo "github-mcp-server binary missing at ${BIN}" >&2
  echo "Download: curl -fsSL -o bin/github-mcp-server.tar.gz https://github.com/github/github-mcp-server/releases/latest/download/github-mcp-server_Darwin_arm64.tar.gz && tar -xzf bin/github-mcp-server.tar.gz -C bin && chmod +x bin/github-mcp-server" >&2
  exit 1
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  if command -v gh >/dev/null 2>&1; then
    GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null || true)"
    export GITHUB_PERSONAL_ACCESS_TOKEN
  fi
fi

if [[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]]; then
  echo "GitHub MCP: set GITHUB_PERSONAL_ACCESS_TOKEN or run 'gh auth login'" >&2
  exit 1
fi

exec "${BIN}" stdio "$@"
