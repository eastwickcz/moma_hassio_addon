#!/usr/bin/with-contenv bashio
set -euo pipefail

export NAYAX_BASE_URL="$(bashio::config 'nayax_base_url')"
export NAYAX_TOKEN="$(bashio::config 'nayax_token')"
export POLL_INTERVAL="$(bashio::config 'poll_interval')"
export SCREEN_TYPE_ID="$(bashio::config 'screen_type_id')"
export ENTITY_ID="$(bashio::config 'entity_id')"
export WIDGET_IDS="$(bashio::config 'widget_ids' | tr -d '[] ' )"
export WIDGET_FILTERS_JSON="$(bashio::config 'widget_filters_json')"
export DEVICE_QUERY="$(bashio::config 'device_query')"
export VERIFY_SSL="$(bashio::config 'verify_ssl')"
export ENTITY_PREFIX="$(bashio::config 'entity_prefix')"
export LOG_LEVEL="$(bashio::config 'log_level')"

if bashio::var.is_empty "${NAYAX_TOKEN}"; then
  bashio::log.fatal "Config 'nayax_token' is required"
  exit 1
fi

if bashio::var.is_empty "${SUPERVISOR_TOKEN:-}"; then
  bashio::log.fatal "SUPERVISOR_TOKEN not available. Ensure 'homeassistant_api: true' in config.yaml"
  exit 1
fi

exec python /app/main.py
