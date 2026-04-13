#!/usr/bin/with-contenv bashio

bashio::log.info "=== Nayax Telemetry Bridge starting ==="

export NAYAX_BASE_URL="$(bashio::config 'nayax_base_url')"
export NAYAX_TOKEN="$(bashio::config 'nayax_token')"
export POLL_INTERVAL="$(bashio::config 'poll_interval')"
export SCREEN_TYPE_ID="$(bashio::config 'screen_type_id')"
export ENTITY_ID="$(bashio::config 'entity_id')"

# widget_ids is a JSON array – read raw value, strip brackets and spaces
WIDGET_IDS_RAW="$(bashio::config 'widget_ids' 2>/dev/null || echo '[]')"
export WIDGET_IDS="$(echo "${WIDGET_IDS_RAW}" | tr -d '[] ')"

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
  bashio::log.fatal "SUPERVISOR_TOKEN not available."
  exit 1
fi

bashio::log.info "Config loaded, launching Python bridge..."
bashio::log.info "Base URL: ${NAYAX_BASE_URL}"
bashio::log.info "Poll interval: ${POLL_INTERVAL}s"

exec python3 /app/main.py
