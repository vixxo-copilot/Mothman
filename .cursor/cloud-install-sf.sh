#!/usr/bin/env bash
# Cursor Cloud install: Freshdesk shell auth + Salesforce JWT auth + repo deps.
# Secrets (set in Cloud Agents -> Environments -> Secrets):
#   FRESHDESK_API_KEY        Freshdesk API key for shell REST scripts and MCP
#   FRESHDESK_TOKEN          Alternate name accepted for Freshdesk API key
#   FRESHDESK_API_KEY_B64    Optional base64-encoded Freshdesk API key
#   SF_CLIENT_ID              Connected App consumer key
#   SF_USERNAME               e.g. crystal.gagner@vixxo.com
#   SF_INSTANCE_URL           e.g. https://vixxo.my.salesforce.com
#   SF_ORG_ALIAS              e.g. vixxo (optional; default vixxo)
#   SF_JWT_PRIVATE_KEY        PEM contents of server.key  OR
#   SF_JWT_PRIVATE_KEY_B64    base64-encoded server.key
#
# Idempotent: safe to re-run on cached cloud snapshots.

set -euo pipefail

configure_freshdesk() {
  local home_vixxo="${HOME}/.vixxo"
  local key_file="${home_vixxo}/freshdesk_api_key"
  local freshdesk_key=""

  mkdir -p "${home_vixxo}"
  chmod 700 "${home_vixxo}"

  if [[ -n "${FRESHDESK_API_KEY:-}" ]]; then
    freshdesk_key="${FRESHDESK_API_KEY}"
  elif [[ -n "${FRESHDESK_TOKEN:-}" ]]; then
    freshdesk_key="${FRESHDESK_TOKEN}"
  elif [[ -n "${FRESHDESK_API_TOKEN:-}" ]]; then
    freshdesk_key="${FRESHDESK_API_TOKEN}"
  elif [[ -n "${FRESHDESK_API_KEY_B64:-}" ]]; then
    freshdesk_key="$(printf '%s' "${FRESHDESK_API_KEY_B64}" | base64 --decode)"
  elif [[ -n "${FRESHDESK_TOKEN_B64:-}" ]]; then
    freshdesk_key="$(printf '%s' "${FRESHDESK_TOKEN_B64}" | base64 --decode)"
  fi

  if [[ -n "${freshdesk_key}" ]]; then
    printf '%s' "${freshdesk_key}" > "${key_file}"
    chmod 600 "${key_file}"
    echo "[cloud-install-sf] Freshdesk API key staged at ~/.vixxo/freshdesk_api_key."
  elif [[ -s "${key_file}" || -s "${home_vixxo}/freshdesk_token" ]]; then
    echo "[cloud-install-sf] Existing Freshdesk credential file found."
  else
    echo "[cloud-install-sf] WARN: no FRESHDESK_API_KEY / FRESHDESK_TOKEN — Freshdesk shell scripts and MCP calls will fail until configured."
  fi
}

configure_freshdesk

ORG_ALIAS="${SF_ORG_ALIAS:-vixxo}"
KEY_FILE="${HOME}/.sf/server.key"

echo "[cloud-install-sf] Installing @salesforce/cli (if needed)..."
if ! command -v sf >/dev/null 2>&1; then
  npm install -g @salesforce/cli
else
  echo "[cloud-install-sf] sf already present: $(sf --version 2>/dev/null | head -n1)"
fi

mkdir -p "${HOME}/.sf"
chmod 700 "${HOME}/.sf"

if [[ -n "${SF_JWT_PRIVATE_KEY_B64:-}" ]]; then
  echo "[cloud-install-sf] Writing JWT key from SF_JWT_PRIVATE_KEY_B64..."
  echo "${SF_JWT_PRIVATE_KEY_B64}" | base64 --decode > "${KEY_FILE}"
elif [[ -n "${SF_JWT_PRIVATE_KEY:-}" ]]; then
  echo "[cloud-install-sf] Writing JWT key from SF_JWT_PRIVATE_KEY..."
  # Preserve PEM newlines if the secret was stored with literal \n
  printf '%s\n' "${SF_JWT_PRIVATE_KEY//\\n/$'\n'}" > "${KEY_FILE}"
else
  echo "[cloud-install-sf] WARN: no SF_JWT_PRIVATE_KEY / SF_JWT_PRIVATE_KEY_B64 — skipping Salesforce auth."
  echo "[cloud-install-sf] Salesforce MCP / sf commands will fail until JWT secrets are set."
  npm install
  exit 0
fi
chmod 600 "${KEY_FILE}"

: "${SF_CLIENT_ID:?SF_CLIENT_ID secret is required for JWT login}"
: "${SF_USERNAME:?SF_USERNAME secret is required for JWT login}"
: "${SF_INSTANCE_URL:?SF_INSTANCE_URL secret is required for JWT login}"

echo "[cloud-install-sf] Authorizing org alias '${ORG_ALIAS}' via JWT..."
sf org login jwt \
  --client-id "${SF_CLIENT_ID}" \
  --jwt-key-file "${KEY_FILE}" \
  --username "${SF_USERNAME}" \
  --alias "${ORG_ALIAS}" \
  --instance-url "${SF_INSTANCE_URL}" \
  --set-default

# Do not print access tokens; org display redacts secrets by default.
sf org display --target-org "${ORG_ALIAS}"
sf --version

echo "[cloud-install-sf] Installing repo dependencies..."
npm install

echo "[cloud-install-sf] Done."
