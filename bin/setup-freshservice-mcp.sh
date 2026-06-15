#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "== Freshservice MCP setup =="

if ! python3 -m uv --version >/dev/null 2>&1; then
  echo "Installing uv (provides uvx)..."
  python3 -m pip install --user uv
fi

PY_BIN="$(python3 -m site --user-base)/bin"
if [[ -d "${PY_BIN}" ]]; then
  export PATH="${PY_BIN}:${PATH}"
fi

if ! command -v uvx >/dev/null 2>&1 && ! python3 -m uv tool --help >/dev/null 2>&1; then
  echo "ERROR: uv/uvx still not available after install." >&2
  exit 1
fi

echo "Checking freshservice-mcp availability..."
if command -v uvx >/dev/null 2>&1; then
  # Avoid stdio servers that block; a dry package resolve is enough.
  uvx --from freshservice-mcp python -c "print('freshservice-mcp ok')" >/dev/null 2>&1 || \
    echo "Note: first Cursor start may download freshservice-mcp once."
else
  python3 -m uv tool install freshservice-mcp >/dev/null 2>&1 || \
    echo "Note: first Cursor start may download freshservice-mcp once."
fi

if [[ ! -f "${ROOT}/.env" ]]; then
  if [[ -f "${ROOT}/.env.example" ]]; then
    cp "${ROOT}/.env.example" "${ROOT}/.env"
    echo "Created ${ROOT}/.env from .env.example"
  else
    cat > "${ROOT}/.env" <<'EOF'
FRESHSERVICE_API_KEY=
FRESHSERVICE_DOMAIN=vixxo.freshservice.com
EOF
    echo "Created ${ROOT}/.env"
  fi
else
  echo ".env already exists"
fi

mkdir -p "${HOME}/.vixxo"
chmod 700 "${HOME}/.vixxo" 2>/dev/null || true

if [[ -z "${FRESHSERVICE_API_KEY:-}" ]] && [[ -f "${ROOT}/.env" ]]; then
  # shellcheck disable=SC1090
  source /dev/null
  val="$(grep -E '^FRESHSERVICE_API_KEY=' "${ROOT}/.env" | head -1 | cut -d= -f2- || true)"
  if [[ -n "${val}" ]]; then
    export FRESHSERVICE_API_KEY="${val}"
  fi
fi

if [[ -n "${FRESHSERVICE_API_KEY:-}" ]]; then
  echo "FRESHSERVICE_API_KEY is configured."
  echo "Restart freshservice MCP in Cursor (Settings → MCP)."
else
  cat <<EOF

Next step — add your Freshservice API key (required):

  Option A (recommended): edit .env
    Open: ${ROOT}/.env
    Set:  FRESHSERVICE_API_KEY=your_key_here

  Option B: key file
    mkdir -p ~/.vixxo
    printf '%s' 'YOUR_KEY' > ~/.vixxo/freshservice_api_key
    chmod 600 ~/.vixxo/freshservice_api_key

Get the key: Freshservice → Profile Settings → API Settings

Then restart the freshservice MCP in Cursor.
EOF
fi

echo "Done."
